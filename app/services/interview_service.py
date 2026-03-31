"""
Interview Service
Orchestrates both:
  - Section 1: AI Practice  (adaptive difficulty + immediate feedback)
  - Section 2: Mock Interview (adaptive difficulty + end-only gap analysis)
"""
import random
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.interview_system import (
    DifficultyLevel,
    InterviewSession,
    KeySkill,
    Question,
    UserResponse,
)
from app.services.question_service import (
    evaluate_answer,
    generate_gap_analysis,
    generate_qa_for_keyword,
)
from app.services.transcribe import transcribe_audio
from app.services.confidence_analyzer import extract_audio_features, compute_confidence
from app.config.settings import settings


# ── Helpers ──────────────────────────────────────────────────────────────────

def _next_difficulty(current: DifficultyLevel, is_correct: bool) -> DifficultyLevel:
    """
    Adaptive difficulty rule:
      - Correct  → move up one level (or stay at Hard)
      - Incorrect → stay at the same level
    """
    ladder = [DifficultyLevel.EASY, DifficultyLevel.MEDIUM, DifficultyLevel.HARD]
    idx = ladder.index(current)
    if is_correct and idx < len(ladder) - 1:
        return ladder[idx + 1]
    return current  # stay at same level on wrong answer


async def _fetch_question(
    db: AsyncSession,
    skill_id: UUID,
    difficulty: DifficultyLevel,
    exclude_ids: list[UUID],
) -> Question | None:
    """Fetch an unused question from the DB for a given skill and difficulty."""
    stmt = (
        select(Question)
        .where(
            Question.skill_id == skill_id,
            Question.difficulty == difficulty,
            Question.id.notin_(exclude_ids),
        )
        .limit(1)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def _get_skills_for_user(db: AsyncSession, user_id: str) -> list[KeySkill]:
    """Return all skills stored for the user."""
    result = await db.execute(select(KeySkill).where(KeySkill.user_id == user_id))
    return list(result.scalars().all())


# ── Keyword Ingestion ────────────────────────────────────────────────────────

async def ingest_keywords_and_generate(
    db: AsyncSession, user_id: str, keywords: list[str]
) -> list[KeySkill]:
    """
    Receives keywords from the teammate's module.
    Saves them to key_skills and generates Easy/Medium/Hard Q&A for each.
    """
    skills: list[KeySkill] = []
    for keyword in keywords:
        skill = KeySkill(user_id=user_id, keyword=keyword)
        db.add(skill)
        await db.flush()  # get the skill.id before generating questions

        for difficulty in DifficultyLevel:
            for _ in range(3):  # Generate 3 questions per level
                q_text, options, a_text = await generate_qa_for_keyword(keyword, difficulty)
                if q_text:
                    db.add(Question(
                        skill_id=skill.id,
                        text=q_text,
                        options=options,
                        answer_key=a_text,
                        difficulty=difficulty,
                    ))
        skills.append(skill)

    await db.commit()
    return skills


# ── Section 1: AI Practice ────────────────────────────────────────────────────

async def get_practice_question(
    db: AsyncSession,
    user_id: str,
    difficulty: DifficultyLevel | None = None,
    exclude_ids: list[UUID] | None = None,
) -> Question | None:
    """Fetch any question at the requested difficulty for the user."""
    # Performance-based logic: if difficulty is None, find last performance
    if difficulty is None:
        stmt = (
            select(UserResponse, Question)
            .join(Question, UserResponse.question_id == Question.id)
            .join(KeySkill, Question.skill_id == KeySkill.id)
            .where(KeySkill.user_id == user_id, UserResponse.session_id == None)
            .order_by(UserResponse.created_at.desc())
            .limit(1)
        )
        result = await db.execute(stmt)
        last_row = result.first()
        if last_row:
            last_resp, last_q = last_row
            difficulty = _next_difficulty(last_q.difficulty, last_resp.is_correct or False)
        else:
            difficulty = DifficultyLevel.EASY

    skills = await _get_skills_for_user(db, user_id)
    if not skills:
        return None
    
    # Randomize skill selection for variety
    random.shuffle(skills)
    
    exclude = exclude_ids or []
    for skill in skills:
        q = await _fetch_question(db, skill.id, difficulty, exclude)
        if q:
            return q
    return None


async def submit_practice_answer(
    db: AsyncSession,
    user_id: str,
    question_id: UUID,
    user_answer: str | None = None,
    audio_path: str | None = None,
) -> dict:
    """
    Section 1 logic:
    1. Evaluate answer immediately via simple comparison.
    2. Show feedback to the user.
    3. Determine the next question's difficulty adaptively.
    4. Return the next question (or mark practice complete).
    """
    # Load the answered question
    result = await db.execute(select(Question).where(Question.id == question_id))
    question = result.scalar_one_or_none()
    if not question:
        return {"error": "Question not found"}

    # Handle Audio if provided
    transcription = None
    confidence_score = None
    audio_metadata = None

    if audio_path:
        transcription = await transcribe_audio(audio_path)
        audio_metadata = extract_audio_features(audio_path, transcription)
        confidence_score = compute_confidence(audio_metadata)
        user_answer = transcription

    if not user_answer:
        return {"error": "No answer provided."}

    # Evaluate
    is_correct, feedback = await evaluate_answer(question.text, question.answer_key, user_answer)

    # Save the user's response
    response_record = UserResponse(
        session_id=None,  # No session in practice mode
        question_id=question_id,
        user_answer=user_answer,
        confidence_score=confidence_score,
        audio_metadata=audio_metadata,
        is_correct=is_correct,
        feedback=feedback,
    )
    db.add(response_record)
    await db.commit()

    # Determine next difficulty
    next_difficulty = _next_difficulty(question.difficulty, is_correct)

    # Fetch next question (exclude already answered one)
    next_question = await get_practice_question(
        db, user_id, next_difficulty, exclude_ids=[question_id]
    )

    return {
        "is_correct": is_correct,
        "feedback": feedback,
        "next_question": next_question,
        "practice_complete": next_question is None,
        "transcription": transcription,
        "confidence_score": confidence_score,
    }


# ── Section 2: Mock Interview ─────────────────────────────────────────────────

async def start_interview_session(db: AsyncSession, user_id: str) -> dict:
    """
    Creates a new interview session and returns the first Easy question.
    """
    skills = await _get_skills_for_user(db, user_id)
    if not skills:
        return {"error": "No skills found for user. Please ingest keywords first."}

    # Create session
    session = InterviewSession(user_id=user_id, status="active")
    db.add(session)
    await db.flush()

    # First question is always Easy, picked from a random skill
    random.shuffle(skills)
    first_question = await _fetch_question(db, skills[0].id, DifficultyLevel.EASY, [])
    if not first_question:
        return {"error": "No questions available. Please generate questions first."}

    # Store the first question ID in feedback as the 'current' question
    session.feedback = str(first_question.id)

    await db.commit()
    return {"session": session, "current_question": first_question}


async def submit_interview_answer(
    db: AsyncSession,
    session_id: UUID,
    user_answer: str | None = None,
    audio_path: str | None = None,
) -> dict:
    """
    Section 2 logic:
    1. Secretly evaluate the answer (NOT shown to user).
    2. Adaptively determine the next question's difficulty.
    3. If last question → generate Gap Analysis.
    4. Return only the next question (or session_complete flag).
    """
    # Load session with responses
    result = await db.execute(
        select(InterviewSession)
        .where(InterviewSession.id == session_id)
        .options(selectinload(InterviewSession.responses))
    )
    session = result.scalar_one_or_none()
    if not session or session.status != "active":
        return {"error": "Session not found or already completed."}

    # Get the last answered question to know current difficulty + skill
    last_response = session.responses[-1] if session.responses else None

    # Load the current (pending) question — we track via a "current_question_id" in session
    # We store the current question id in the session feedback field temporarily
    current_q_id = UUID(session.feedback) if session.feedback and len(session.feedback) == 36 else None  # noqa: PLR2004
    if not current_q_id:
        return {"error": "No active question found for this session."}

    q_result = await db.execute(select(Question).where(Question.id == current_q_id))
    current_question = q_result.scalar_one_or_none()
    if not current_question:
        return {"error": "Question not found."}

    # Handle Audio if provided
    transcription = None
    confidence_score = None
    audio_metadata = None

    if audio_path:
        transcription = await transcribe_audio(audio_path)
        audio_metadata = extract_audio_features(audio_path, transcription)
        confidence_score = compute_confidence(audio_metadata)
        user_answer = transcription  # transcription becomes the answer text for evaluation

    if not user_answer:
        return {"error": "No answer provided (neither text nor audio)."}

    # Secretly evaluate
    is_correct, feedback = await evaluate_answer(
        current_question.text, current_question.answer_key, user_answer
    )

    # Save response with hidden result
    response_record = UserResponse(
        session_id=session_id,
        question_id=current_q_id,
        user_answer=user_answer,
        confidence_score=confidence_score,
        audio_metadata=audio_metadata,
        is_correct=is_correct,
        feedback=feedback if not session_id else None, # Feedback only for practice (non-session)
    )
    db.add(response_record)
    await db.flush()

    # Determine next difficulty
    next_difficulty = _next_difficulty(current_question.difficulty, is_correct)

    # Get all answered question IDs (for excluding them from next selection)
    answered_ids = [r.question_id for r in session.responses if r.question_id]
    answered_ids.append(current_q_id)

    # Calculate elapsed time (5-minute limit)
    now = datetime.utcnow()
    elapsed_seconds = (now - session.created_at).total_seconds()

    if elapsed_seconds >= 300: # 300 seconds = 5 minutes
        next_question = None
    else:
        # Try to get the next skill to vary questions across skills
        all_skills = await _get_skills_for_user(db, session.user_id)
        random.shuffle(all_skills)
        next_question = None
        for skill in all_skills:
            next_q = await _fetch_question(db, skill.id, next_difficulty, answered_ids)
            if next_q:
                next_question = next_q
                break

    if next_question:
        # Store next question id in session.feedback temporarily
        session.feedback = str(next_question.id)
        await db.commit()
        return {
            "session_complete": False, 
            "next_question": next_question,
            "transcription": transcription,
            "confidence_score": confidence_score,
        }
    else:
        # No more questions → generate Gap Analysis
        all_responses_result = await db.execute(
            select(UserResponse, Question)
            .join(Question, UserResponse.question_id == Question.id)
            .where(UserResponse.session_id == session_id)
        )
        history = [
            {
                "question": row.Question.text,
                "user_answer": row.UserResponse.user_answer,
                "is_correct": row.UserResponse.is_correct or False,
                "confidence": row.UserResponse.confidence_score,
            }
            for row in all_responses_result.all()
        ]

        gap_analysis = await generate_gap_analysis(history)
        session.feedback = gap_analysis
        session.status = "completed"
        await db.commit()
        return {
            "session_complete": True, 
            "next_question": None,
            "transcription": transcription,
            "confidence_score": confidence_score,
        }


async def get_session_feedback(db: AsyncSession, session_id: UUID) -> dict:
    """Return the Gap Analysis feedback for a completed session."""
    result = await db.execute(
        select(InterviewSession).where(InterviewSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        return {"error": "Session not found."}
    if session.status != "completed":
        return {"error": "Session is still active. Complete the interview first."}
    return {
        "session_id": session_id,
        "feedback": session.feedback,
    }

from sqlalchemy import select
from app.models.interview_system import InterviewSession

async def get_user_sessions(db, user_id: str):
    result = await db.execute(
        select(InterviewSession).where(
            InterviewSession.user_id == user_id,
            InterviewSession.deleted_at.is_(None)
        )
    )
    return result.scalars().all()
