"""
Interview Service
Orchestrates both:
  - Section 1: AI Practice  (adaptive difficulty + immediate feedback)
  - Section 2: Mock Interview (adaptive difficulty + end-only gap analysis)

All user input is audio — Whisper handles transcription before this service is called.
No text fallback; audio_path is always expected.
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
    segment_transcript,
)
from app.services.transcribe import transcribe_audio
from app.services.confidence_analyzer import extract_audio_features, compute_confidence
from app.config.settings import settings

# Minimum number of unasked questions before auto-generation is triggered
MIN_QUESTION_THRESHOLD = 3


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
            Question.id.notin_(exclude_ids) if exclude_ids else True,
        )
        .limit(1)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def _get_skills_for_user(db: AsyncSession, user_id: str) -> list[KeySkill]:
    """Return all skills stored for the user."""
    result = await db.execute(select(KeySkill).where(KeySkill.user_id == user_id))
    return list(result.scalars().all())


async def _get_practice_answered_ids(db: AsyncSession, user_id: str) -> list[UUID]:
    """Return all question IDs the user has answered in Practice (session_id IS NULL)."""
    stmt = (
        select(UserResponse.question_id)
        .join(Question, UserResponse.question_id == Question.id)
        .join(KeySkill, Question.skill_id == KeySkill.id)
        .where(KeySkill.user_id == user_id, UserResponse.session_id.is_(None))
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def _get_prior_mock_answered_ids(db: AsyncSession, user_id: str) -> list[UUID]:
    """Return all question IDs the user has answered in any prior completed mock session."""
    stmt = (
        select(UserResponse.question_id)
        .join(InterviewSession, UserResponse.session_id == InterviewSession.id)
        .where(InterviewSession.user_id == user_id, InterviewSession.status == "completed")
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def _count_available_questions(
    db: AsyncSession, user_id: str, exclude_ids: list[UUID]
) -> int:
    """Count questions not yet answered (not in exclude_ids) for a user's skills."""
    skills = await _get_skills_for_user(db, user_id)
    if not skills:
        return 0
    skill_ids = [s.id for s in skills]
    stmt = select(Question.id).where(
        Question.skill_id.in_(skill_ids),
        Question.id.notin_(exclude_ids) if exclude_ids else True,
    )
    result = await db.execute(stmt)
    return len(result.scalars().all())


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


async def _regenerate_questions_for_user(db: AsyncSession, user_id: str) -> None:
    """Generate a fresh batch of questions for each of the user's skills."""
    skills = await _get_skills_for_user(db, user_id)
    for skill in skills:
        for difficulty in DifficultyLevel:
            for _ in range(3):
                q_text, options, a_text = await generate_qa_for_keyword(skill.keyword, difficulty)
                if q_text:
                    db.add(Question(
                        skill_id=skill.id,
                        text=q_text,
                        options=options,
                        answer_key=a_text,
                        difficulty=difficulty,
                    ))
    await db.commit()


# ── Section 1: AI Practice ────────────────────────────────────────────────────

async def get_practice_question(
    db: AsyncSession,
    user_id: str,
    difficulty: DifficultyLevel | None = None,
    extra_exclude_ids: list[UUID] | None = None,
) -> Question | None:
    """Fetch any unanswered question at the requested difficulty for the user.
    Always excludes all previously answered practice questions (DB-queried fresh).
    """
    # Always query DB for all practice-answered IDs to prevent repeats
    exclude_ids = await _get_practice_answered_ids(db, user_id)
    if extra_exclude_ids:
        exclude_ids = list(set(exclude_ids) | set(extra_exclude_ids))

    # Performance-based difficulty selection
    if difficulty is None:
        stmt = (
            select(UserResponse, Question)
            .join(Question, UserResponse.question_id == Question.id)
            .join(KeySkill, Question.skill_id == KeySkill.id)
            .where(KeySkill.user_id == user_id, UserResponse.session_id.is_(None))
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

    for skill in skills:
        q = await _fetch_question(db, skill.id, difficulty, exclude_ids)
        if q:
            return q
    return None


async def submit_practice_answer(
    db: AsyncSession,
    user_id: str,
    question_id: UUID,
    audio_path: str,
) -> dict:
    """
    Section 1 logic — Audio-only input:
    1. Transcribe audio via Whisper.
    2. Extract audio features + compute confidence score.
    3. Evaluate answer semantically via LLM.
    4. Return immediate feedback + next question.
    """
    # Load the answered question
    result = await db.execute(select(Question).where(Question.id == question_id))
    question = result.scalar_one_or_none()
    if not question:
        return {"error": "Question not found"}

    # Transcribe audio
    transcription = await transcribe_audio(audio_path)
    audio_metadata = extract_audio_features(audio_path, transcription)
    confidence_score = compute_confidence(audio_metadata)

    # Evaluate semantically
    is_correct, feedback = await evaluate_answer(question.text, question.answer_key, transcription)

    # Save the user's response
    response_record = UserResponse(
        session_id=None,  # No session in practice mode
        question_id=question_id,
        user_answer=transcription,
        confidence_score=confidence_score,
        audio_metadata=audio_metadata,
        is_correct=is_correct,
        feedback=feedback,
    )
    db.add(response_record)
    await db.commit()

    # Determine next difficulty
    next_difficulty = _next_difficulty(question.difficulty, is_correct)

    # Fetch next question (exclude already answered ones, DB-fresh)
    next_question = await get_practice_question(
        db, user_id, next_difficulty, extra_exclude_ids=[question_id]
    )

    return {
        "is_correct": is_correct,
        "feedback": feedback,
        "transcription": transcription,
        "confidence_score": confidence_score,
        "next_question": next_question,
        "practice_complete": next_question is None,
    }


# ── Section 2: Mock Interview ─────────────────────────────────────────────────

# ── Frontend List / Result Endpoints ─────────────────────────────────────────

async def get_user_sessions(db: AsyncSession, user_id: str) -> list[dict]:
    """
    Return a list of all mock interview sessions for a user,
    with the count of responses per session.
    """
    sessions_result = await db.execute(
        select(InterviewSession)
        .where(InterviewSession.user_id == user_id)
        .order_by(InterviewSession.created_at.desc())
        .options(selectinload(InterviewSession.responses))
    )
    sessions = sessions_result.scalars().all()
    return [
        {
            "session_id": s.id,
            "status": s.status,
            "created_at": s.created_at,
            "response_count": len(s.responses),
        }
        for s in sessions
    ]


async def get_session_result(db: AsyncSession, session_id: UUID) -> dict:
    """
    Return the full result for a completed mock session:
    session metadata + gap analysis + all Q&A responses.
    """
    session_result = await db.execute(
        select(InterviewSession).where(InterviewSession.id == session_id)
    )
    session = session_result.scalar_one_or_none()
    if not session:
        return {"error": "Session not found."}
    if session.status != "completed":
        return {"error": "Session is still active. Complete the interview first."}

    # Fetch all responses joined with their questions
    responses_result = await db.execute(
        select(UserResponse, Question)
        .join(Question, UserResponse.question_id == Question.id)
        .where(UserResponse.session_id == session_id)
        .order_by(UserResponse.created_at)
    )
    responses = [
        {
            "question_text": row.Question.text,
            "user_answer": row.UserResponse.user_answer,
            "confidence_score": row.UserResponse.confidence_score,
            "is_correct": row.UserResponse.is_correct,
            "feedback": row.UserResponse.feedback,
        }
        for row in responses_result.all()
    ]

    return {
        "session_id": session.id,
        "status": session.status,
        "gap_analysis": session.feedback,
        "responses": responses,
    }


# ── Batch Audio Mock Interview (5-Minute Session) ───────────────────────────

async def start_batch_interview(db: AsyncSession, user_id: str) -> dict:
    """
    Starts a compulsory 5-minute mock session by providing 15 questions upfront.
    The user will answer as many as possible in one long audio recording.
    """
    skills = await _get_skills_for_user(db, user_id)
    if not skills:
        return {"error": "No skills found for user. Please ingest keywords first."}

    # Build global exclusion
    practice_ids = await _get_practice_answered_ids(db, user_id)
    prior_mock_ids = await _get_prior_mock_answered_ids(db, user_id)
    globally_excluded = list(set(practice_ids) | set(prior_mock_ids))

    # Auto-generate if pool is shallow
    available = await _count_available_questions(db, user_id, globally_excluded)
    if available < 15:  # Need at least 15 for a full 5-minute batch
        await _regenerate_questions_for_user(db, user_id)

    # Pick 15 questions: 5 Easy, 5 Medium, 5 Hard
    batch_questions: list[Question] = []
    difficulties = [
        DifficultyLevel.EASY, DifficultyLevel.EASY, DifficultyLevel.EASY, DifficultyLevel.EASY, DifficultyLevel.EASY,
        DifficultyLevel.MEDIUM, DifficultyLevel.MEDIUM, DifficultyLevel.MEDIUM, DifficultyLevel.MEDIUM, DifficultyLevel.MEDIUM,
        DifficultyLevel.HARD, DifficultyLevel.HARD, DifficultyLevel.HARD, DifficultyLevel.HARD, DifficultyLevel.HARD
    ]
    
    # Shuffle skills to spread questions across topics
    random.shuffle(skills)
    skill_cycle = 0
    
    current_excluded = list(globally_excluded)
    for target_diff in difficulties:
        picked = None
        for _ in range(len(skills)):
            skill = skills[skill_cycle % len(skills)]
            skill_cycle += 1
            picked = await _fetch_question(db, skill.id, target_diff, current_excluded)
            if picked:
                batch_questions.append(picked)
                current_excluded.append(picked.id)
                break
        if not picked:
            for skill in skills:
                picked = await _fetch_question(db, skill.id, DifficultyLevel.EASY, current_excluded) or \
                         await _fetch_question(db, skill.id, DifficultyLevel.MEDIUM, current_excluded) or \
                         await _fetch_question(db, skill.id, DifficultyLevel.HARD, current_excluded)
                if picked:
                    batch_questions.append(picked)
                    current_excluded.append(picked.id)
                    break

    if not batch_questions:
        return {"error": "No questions available. Please ingest more keywords."}

    # Create session
    import json
    session = InterviewSession(user_id=user_id, status="active")
    session.feedback = json.dumps({"batch_ids": [str(q.id) for q in batch_questions]})
    db.add(session)
    await db.commit()
    
    return {"session_id": session.id, "questions": batch_questions}


async def submit_batch_answer(
    db: AsyncSession,
    session_id: UUID,
    audio_path: str,
) -> dict:
    """
    Processes the compulsory 5-minute audio file.
    Enforces a minimum duration of 5 minutes (300 seconds).
    """
    import json
    import librosa
    
    # Check duration (strictly 5 minutes for a full assessment)
    try:
        duration_sec = librosa.get_duration(path=audio_path)
        if duration_sec < 290:  # Minimum 4:50
            return {
                "error": "The recording is too short for a comprehensive evaluation. "
                         "Please provide more detailed responses to the questions provided."
            }
        if duration_sec > 315:  # Maximum 5:15
            return {
                "error": "The recording exceeds the allotted 5-minute time limit. "
                         "Please ensure your session stays within the precise timing."
            }
    except Exception as e:
         return {"error": f"Failed to check audio duration: {str(e)}"}

    # Load session
    result = await db.execute(select(InterviewSession).where(InterviewSession.id == session_id))
    session = result.scalar_one_or_none()
    if not session or session.status != "active":
        return {"error": "Session not found or already completed."}

    # Load question IDs from metadata
    try:
        metadata = json.loads(session.feedback or "{}")
        batch_ids = [UUID(id_str) for id_str in metadata.get("batch_ids", [])]
    except (json.JSONDecodeError, ValueError):
        return {"error": "Invalid session metadata."}

    if not batch_ids:
        return {"error": "No questions found for this session."}

    # Transcribe full audio
    full_transcript = await transcribe_audio(audio_path)
    audio_metadata = extract_audio_features(audio_path, full_transcript)
    confidence_score = compute_confidence(audio_metadata)

    # Fetch question objects to provide texts for segmentation
    q_result = await db.execute(select(Question).where(Question.id.in_(batch_ids)))
    questions = q_result.scalars().all()
    q_map = {q.id: q for q in questions}
    ordered_questions = [q_map[qid] for qid in batch_ids if qid in q_map]

    # Segment transcript
    segments = await segment_transcript([q.text for q in ordered_questions], full_transcript)

    # Evaluate each segment
    responses_list = []
    for idx, answer_text in segments.items():
        if idx >= len(ordered_questions):
            continue
        
        q = ordered_questions[idx]
        is_correct, feedback = await evaluate_answer(q.text, q.answer_key, answer_text)
        
        response_record = UserResponse(
            session_id=session_id,
            question_id=q.id,
            user_answer=answer_text,
            confidence_score=confidence_score,
            audio_metadata=audio_metadata,
            is_correct=is_correct,
            feedback=feedback,
        )
        db.add(response_record)
        responses_list.append({
            "question": q.text,
            "user_answer": answer_text,
            "is_correct": is_correct,
            "confidence": confidence_score
        })

    # Generate Gap Analysis
    if not responses_list:
        gap_analysis = "No answers were identified in the 5-minute recording."
    else:
        gap_analysis = await generate_gap_analysis(responses_list)

    session.feedback = gap_analysis
    session.status = "completed"
    await db.commit()

    return {
        "session_id": session_id,
        "gap_analysis": gap_analysis,
        "responses_count": len(responses_list),
        "duration_sec": round(duration_sec, 2)
    }




