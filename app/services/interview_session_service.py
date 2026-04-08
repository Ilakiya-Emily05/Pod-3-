
import logging
import random
from datetime import datetime
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import noload

from app.models.interview_system import (
    DifficultyLevel,
    InterviewSession,
    KeySkill,
    Question,
    UserResponse,
)
from app.services.confidence_analyzer import compute_confidence, extract_audio_features
from app.services.interview_helpers import (
    fetch_question,
    get_answered_ids,
    get_previous_completed_score,
    get_response_count,
    get_skills_for_user,
    next_difficulty,
    question_to_dict,
    safe_dict,
    safe_pronunciation,
)
from app.services.pronunciation_analyzer import analyze_pronunciation
from app.services.question_service import (
    evaluate_answer,
    generate_gap_analysis,
    generate_qa_for_keyword,
)
from app.services.session_analytics_service import SessionAnalyticsService
from app.services.transcribe import transcribe_audio

logger = logging.getLogger(__name__)


# ── Keyword Ingestion ─────────────────────────────────────────────────────────


async def ingest_keywords_and_generate(
    db: AsyncSession, user_id: str, keywords: list[str]
) -> list[KeySkill]:
    """Save keywords and generate Easy/Medium/Hard questions for each."""
    skills: list[KeySkill] = []
    for keyword in keywords:
        skill = KeySkill(user_id=user_id, keyword=keyword)
        db.add(skill)
        await db.flush()
        for difficulty in DifficultyLevel:
            for _ in range(3):
                q_text, options, a_text = await generate_qa_for_keyword(keyword, difficulty)
                if q_text:
                    db.add(
                        Question(
                            skill_id=skill.id,
                            text=q_text,
                            options=options,
                            answer_key=a_text,
                            difficulty=difficulty,
                        )
                    )
        skills.append(skill)
    await db.commit()
    return skills


async def _regenerate_questions(db: AsyncSession, user_id: str) -> None:
    """Generate a fresh batch of questions for all user skills."""
    skills = await get_skills_for_user(db, user_id)
    for skill in skills:
        for difficulty in DifficultyLevel:
            for _ in range(3):
                q_text, options, a_text = await generate_qa_for_keyword(skill.keyword, difficulty)
                if q_text:
                    db.add(
                        Question(
                            skill_id=skill.id,
                            text=q_text,
                            options=options,
                            answer_key=a_text,
                            difficulty=difficulty,
                        )
                    )
    await db.commit()


# ── Section 1: AI Practice ────────────────────────────────────────────────────


async def get_practice_question(
    db: AsyncSession,
    user_id: str,
    difficulty: DifficultyLevel | None = None,
    extra_exclude_ids: list[UUID] | None = None,
) -> Question | None:
    """Fetch the next adaptive practice question for a user."""
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
            difficulty = next_difficulty(last_q.difficulty, last_resp.is_correct or False)
        else:
            difficulty = DifficultyLevel.EASY

    skills = await get_skills_for_user(db, user_id)
    if not skills:
        return None

    random.shuffle(skills)
    exclude = extra_exclude_ids or []
    for skill in skills:
        q = await fetch_question(db, skill.id, difficulty, exclude)
        if q:
            return q
    return None


async def submit_practice_answer(
    db: AsyncSession,
    user_id: str,
    question_id: UUID,
    audio_path: str | None = None,
) -> dict:
    """Evaluate a practice answer and return immediate feedback."""
    result = await db.execute(select(Question).where(Question.id == question_id))
    question = result.scalar_one_or_none()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found.")

    transcription: str | None = None
    confidence_score: float | None = None
    audio_metadata: dict | None = None
    user_answer: str | None = None
    pronunciation_result: dict = {}

    if audio_path:
        transcription = await transcribe_audio(audio_path)
        audio_metadata = safe_dict(extract_audio_features(audio_path, transcription))
        confidence_score = compute_confidence(audio_metadata) if audio_metadata else None
        user_answer = transcription
        pronunciation_result = await analyze_pronunciation(question.text, transcription)

    if not user_answer:
        raise HTTPException(status_code=422, detail="No answer provided.")

    is_correct, feedback = await evaluate_answer(question.text, question.answer_key, user_answer)
    safe_p = safe_pronunciation(pronunciation_result)

    db.add(
        UserResponse(
            session_id=None,
            question_id=question_id,
            user_answer=user_answer,
            confidence_score=confidence_score,
            audio_metadata=audio_metadata,
            is_correct=is_correct,
            feedback=feedback,
            answered_at=datetime.utcnow(),
            pronunciation_score=safe_p.get("phoneme_score"),
            pronunciation_data=safe_dict(safe_p),
        )
    )
    await db.commit()

    next_q = await get_practice_question(
        db,
        user_id,
        next_difficulty(question.difficulty, is_correct),
        extra_exclude_ids=[question_id],
    )

    return {
        "is_correct": is_correct,
        "feedback": feedback,
        "transcription": transcription,
        "confidence_score": confidence_score,
        "pronunciation": safe_p,
        "next_question": question_to_dict(next_q) if next_q else None,
        "practice_complete": next_q is None,
    }


# ── Section 2: Mock Interview ─────────────────────────────────────────────────


async def start_interview_session(db: AsyncSession, user_id: str) -> dict:
    """Create a new mock interview session and return the first question."""
    skills = await get_skills_for_user(db, user_id)
    if not skills:
        raise HTTPException(
            status_code=404,
            detail="No skills found. Please ingest keywords first.",
        )

    session = InterviewSession(user_id=user_id, status="active", started_at=datetime.utcnow())
    db.add(session)
    await db.flush()

    random.shuffle(skills)
    first_question: Question | None = None
    for skill in skills:
        first_question = await fetch_question(db, skill.id, DifficultyLevel.EASY, [])
        if first_question:
            break

    if not first_question:
        raise HTTPException(status_code=404, detail="No questions available.")

    session.feedback = str(first_question.id)
    await db.commit()

    return {
        "session_id": str(session.id),
        "status": session.status,
        "current_question": question_to_dict(first_question),
    }


async def submit_batch_answer(
    db: AsyncSession,
    session_id: UUID,
    audio_path: str | None = None,
    user_answer: str | None = None,
) -> dict:
    """
    Submit an answer for the current mock interview question.
    Handles transcription, pronunciation analysis, adaptive difficulty,
    and session completion with gap analysis + analytics update.
    """
    result = await db.execute(
        select(InterviewSession).where(InterviewSession.id == session_id).options(noload("*"))
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    if session.status != "active":
        raise HTTPException(status_code=400, detail="Session already completed.")

    response_count = await get_response_count(db, session_id)
    answered_ids = await get_answered_ids(db, session_id)

    current_q_id_str = session.feedback
    if not current_q_id_str or len(current_q_id_str) != 36:
        raise HTTPException(status_code=400, detail="No active question for this session.")

    current_q_id = UUID(current_q_id_str)
    q_result = await db.execute(select(Question).where(Question.id == current_q_id))
    current_question = q_result.scalar_one_or_none()
    if not current_question:
        raise HTTPException(status_code=404, detail="Question not found.")

    transcription: str | None = None
    confidence_score: float | None = None
    audio_metadata: dict | None = None
    pronunciation_result: dict = {}

    if audio_path:
        transcription = await transcribe_audio(audio_path)
        audio_metadata = safe_dict(extract_audio_features(audio_path, transcription))
        confidence_score = compute_confidence(audio_metadata) if audio_metadata else None
        user_answer = transcription
        pronunciation_result = await analyze_pronunciation(
            reference_text=current_question.text,
            transcript=transcription,
        )

    if not user_answer:
        raise HTTPException(status_code=422, detail="No answer provided.")

    is_correct, _ = await evaluate_answer(
        current_question.text, current_question.answer_key, user_answer
    )
    safe_p = safe_pronunciation(pronunciation_result)

    db.add(
        UserResponse(
            session_id=session_id,
            question_id=current_q_id,
            user_answer=user_answer,
            confidence_score=confidence_score,
            audio_metadata=audio_metadata,
            is_correct=is_correct,
            feedback=None,
            question_index=response_count,
            answered_at=datetime.utcnow(),
            pronunciation_score=safe_p.get("phoneme_score"),
            pronunciation_data=safe_dict(safe_p)
            if any(v is not None for v in safe_p.values())
            else None,
        )
    )
    await db.commit()

    answered_ids = [*answered_ids, current_q_id]
    elapsed = (datetime.utcnow() - session.started_at).total_seconds() if session.started_at else 0

    next_q: Question | None = None
    if elapsed < 300:
        all_skills = await get_skills_for_user(db, session.user_id)
        random.shuffle(all_skills)
        diff = next_difficulty(current_question.difficulty, is_correct)
        for skill in all_skills:
            candidate = await fetch_question(db, skill.id, diff, answered_ids)
            if candidate:
                next_q = candidate
                break

    if next_q:
        session.feedback = str(next_q.id)
        await db.commit()
        return {
            "session_complete": False,
            "next_question": question_to_dict(next_q),
            "transcription": transcription,
            "confidence_score": confidence_score,
            "pronunciation": safe_p,
        }

    return await _finalise_session(db, session, session_id, transcription, confidence_score, safe_p)


async def _finalise_session(
    db: AsyncSession,
    session: InterviewSession,
    session_id: UUID,
    transcription: str | None,
    confidence_score: float | None,
    safe_p: dict,
) -> dict:
    """Complete a session: gap analysis, scoring, analytics update."""
    rows_result = await db.execute(
        select(UserResponse, Question)
        .join(Question, UserResponse.question_id == Question.id)
        .where(UserResponse.session_id == session_id)
    )
    rows = rows_result.all()

    history = [
        {
            "question": row.Question.text,
            "user_answer": row.UserResponse.user_answer,
            "is_correct": row.UserResponse.is_correct or False,
            "confidence": row.UserResponse.confidence_score,
        }
        for row in rows
    ]

    gap_analysis = await generate_gap_analysis(history)
    total = len(rows)
    correct = sum(1 for row in rows if row.UserResponse.is_correct)
    overall_score = round((correct / total) * 100) if total > 0 else 0

    previous_score = await get_previous_completed_score(db, session.user_id)
    improvement_delta = (
        round(overall_score - previous_score, 2) if previous_score is not None else None
    )

    ended_at = datetime.utcnow()
    duration_mins = (
        round((ended_at - session.started_at).total_seconds() / 60) if session.started_at else None
    )

    session.feedback = gap_analysis
    session.status = "completed"
    session.ended_at = ended_at
    session.duration_mins = duration_mins
    session.overall_score = overall_score
    session.improvement_delta = improvement_delta
    await db.commit()

    analytics_svc = SessionAnalyticsService(db)
    await analytics_svc.update(session.user_id, session)
    skills = await get_skills_for_user(db, session.user_id)
    await analytics_svc.save_skill_scores(session.user_id, session.id, skills, overall_score)

    return {
        "session_complete": True,
        "next_question": None,
        "transcription": transcription,
        "confidence_score": confidence_score,
        "pronunciation": safe_p,
    }


async def get_session_feedback(db: AsyncSession, session_id: UUID) -> dict:
    """Return the Gap Analysis for a completed session."""
    result = await db.execute(select(InterviewSession).where(InterviewSession.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    if session.status != "completed":
        raise HTTPException(status_code=400, detail="Session is still active.")
    return {"session_id": str(session_id), "feedback": session.feedback}
