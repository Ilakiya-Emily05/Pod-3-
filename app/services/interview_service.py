"""
Interview Service — Sprint 2 Task 1 (Final)
Fixes:
  - get_session_result now defined (was missing → replay crash)
  - get_user_sessions uses DB-level pagination (not in-memory slicing)
  - audio_url field used correctly (was r.audio_url on wrong field)
  - improvement_delta calculated and saved on session completion
  - started_at stamped on session start
  - ended_at + duration_mins stamped on session completion
  - question_index + answered_at saved per UserResponse
"""
import random
from datetime import datetime
from uuid import UUID

from sqlalchemy import select, func
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

# Minimum number of unasked questions before auto-generation is triggered
MIN_QUESTION_THRESHOLD = 3


# ── Helpers ──────────────────────────────────────────────────────────────────

def _next_difficulty(current: DifficultyLevel, is_correct: bool) -> DifficultyLevel:
    ladder = [DifficultyLevel.EASY, DifficultyLevel.MEDIUM, DifficultyLevel.HARD]
    idx = ladder.index(current)
    if is_correct and idx < len(ladder) - 1:
        return ladder[idx + 1]
    return current


async def _fetch_question(
    db: AsyncSession,
    skill_id: UUID,
    difficulty: DifficultyLevel,
    exclude_ids: list[UUID],
) -> Question | None:
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
    result = await db.execute(select(KeySkill).where(KeySkill.user_id == user_id))
    return list(result.scalars().all())


async def _get_previous_completed_score(db: AsyncSession, user_id: str) -> int | None:
    """Get overall_score of the most recent completed session for improvement delta."""
    stmt = (
        select(InterviewSession.overall_score)
        .where(
            InterviewSession.user_id == user_id,
            InterviewSession.status == "completed",
            InterviewSession.overall_score.isnot(None),
            InterviewSession.deleted_at.is_(None),
        )
        .order_by(InterviewSession.created_at.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


# ── Keyword Ingestion ─────────────────────────────────────────────────────────

async def ingest_keywords_and_generate(
    db: AsyncSession, user_id: str, keywords: list[str]
) -> list[KeySkill]:
    skills: list[KeySkill] = []
    for keyword in keywords:
        skill = KeySkill(user_id=user_id, keyword=keyword)
        db.add(skill)
        await db.flush()
        for difficulty in DifficultyLevel:
            for _ in range(3):
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

    random.shuffle(skills)
    exclude = extra_exclude_ids or []
    for skill in skills:
        q = await _fetch_question(db, skill.id, difficulty, exclude)
        if q:
            return q
    return None


async def submit_practice_answer(
    db: AsyncSession,
    user_id: str,
    question_id: UUID,
    audio_path: str,
) -> dict:
    result = await db.execute(select(Question).where(Question.id == question_id))
    question = result.scalar_one_or_none()
    if not question:
        return {"error": "Question not found"}

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

    is_correct, feedback = await evaluate_answer(question.text, question.answer_key, user_answer)

    response_record = UserResponse(
        session_id=None,
        question_id=question_id,
        user_answer=transcription,
        confidence_score=confidence_score,
        audio_metadata=audio_metadata,
        is_correct=is_correct,
        feedback=feedback,
        answered_at=datetime.utcnow(),
    )
    db.add(response_record)
    await db.commit()

    next_difficulty = _next_difficulty(question.difficulty, is_correct)
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

async def start_interview_session(db: AsyncSession, user_id: str) -> dict:
    """Creates a new interview session, stamps started_at, returns first question."""
    skills = await _get_skills_for_user(db, user_id)
    if not skills:
        return {"error": "No skills found for user. Please ingest keywords first."}

    session = InterviewSession(
        user_id=user_id,
        status="active",
        started_at=datetime.utcnow(),
    )
    db.add(session)
    await db.flush()

    random.shuffle(skills)
    first_question = None
    for skill in skills:
        first_question = await _fetch_question(db, skill.id, DifficultyLevel.EASY, [])
        if first_question:
            break

    session.feedback = str(first_question.id)
    await db.commit()

    return {"session": session, "current_question": first_question}


async def submit_batch_answer(
    db: AsyncSession,
    session_id: UUID,
    audio_path: str,
) -> dict:
    """
    Submit answer to current question.
    Tracks question_index, answered_at per response.
    On session completion: stamps ended_at, duration_mins,
    calculates overall_score and improvement_delta.
    """
    result = await db.execute(
        select(InterviewSession)
        .where(InterviewSession.id == session_id)
        .options(selectinload(InterviewSession.responses))
    )
    session = result.scalar_one_or_none()
    if not session or session.status != "active":
        return {"error": "Session not found or already completed."}

    current_q_id_str = session.feedback
    if not current_q_id_str or len(current_q_id_str) != 36:  # noqa: PLR2004
        return {"error": "No active question found for this session."}

    current_q_id = UUID(current_q_id_str)
    q_result = await db.execute(select(Question).where(Question.id == current_q_id))
    current_question = q_result.scalar_one_or_none()
    if not current_question:
        return {"error": "Question not found."}

    transcription = None
    confidence_score = None
    audio_metadata = None

    if audio_path:
        transcription = await transcribe_audio(audio_path)
        audio_metadata = extract_audio_features(audio_path, transcription)
        confidence_score = compute_confidence(audio_metadata)
        user_answer = transcription

    if not user_answer:
        return {"error": "No answer provided (neither text nor audio)."}

    is_correct, feedback = await evaluate_answer(
        current_question.text, current_question.answer_key, user_answer
    )

    current_index = len(session.responses)

    response_record = UserResponse(
        session_id=session_id,
        question_id=current_q_id,
        user_answer=user_answer,
        confidence_score=confidence_score,
        audio_metadata=audio_metadata,
        is_correct=is_correct,
        feedback=None,
        question_index=current_index,
        answered_at=datetime.utcnow(),
    )
    db.add(response_record)
    await db.flush()

    next_difficulty = _next_difficulty(current_question.difficulty, is_correct)
    answered_ids = [r.question_id for r in session.responses] + [current_q_id]

    now = datetime.utcnow()
    elapsed_seconds = (now - session.started_at).total_seconds() if session.started_at else 0

    next_question = None
    if elapsed_seconds < 300:
        all_skills = await _get_skills_for_user(db, session.user_id)
        random.shuffle(all_skills)
        for skill in all_skills:
            next_q = await _fetch_question(db, skill.id, next_difficulty, answered_ids)
            if next_q:
                next_question = next_q
                break

    if next_question:
        session.feedback = str(next_question.id)
        await db.commit()
        return {
            "session_complete": False,
            "next_question": next_question,
            "transcription": transcription,
            "confidence_score": confidence_score,
        }

    # ── Session complete: finalize all metrics ────────────────────
    all_responses_result = await db.execute(
        select(UserResponse, Question)
        .join(Question, UserResponse.question_id == Question.id)
        .where(UserResponse.session_id == session_id)
    )
    rows = all_responses_result.all()

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

    previous_score = await _get_previous_completed_score(db, session.user_id)
    improvement_delta = (
        round(overall_score - previous_score, 2) if previous_score is not None else None
    )

    ended_at = datetime.utcnow()
    duration_mins = (
        round((ended_at - session.started_at).total_seconds() / 60)
        if session.started_at else None
    )

    session.feedback = gap_analysis
    session.status = "completed"
    session.ended_at = ended_at
    session.duration_mins = duration_mins
    session.overall_score = overall_score
    session.improvement_delta = improvement_delta

    await db.commit()

    return {
        "session_complete": True,
        "next_question": None,
        "transcription": transcription,
        "confidence_score": confidence_score,
    }


async def get_session_feedback(db: AsyncSession, session_id: UUID) -> dict:
    """Return Gap Analysis for a completed session."""
    result = await db.execute(
        select(InterviewSession).where(InterviewSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        return {"error": "Session not found."}
    if session.status != "completed":
        return {"error": "Session is still active. Complete the interview first."}
    return {"session_id": session_id, "feedback": session.feedback}


# ── History (DB-level pagination) ─────────────────────────────────────────────

async def get_user_sessions(
    db: AsyncSession,
    user_id: str,
    page: int = 1,
    limit: int = 10,
    interview_type: str | None = None,
) -> dict:
    """
    Returns paginated session history with total count.
    Pagination done at DB level (not in-memory slicing).
    """
    base_query = (
        select(InterviewSession)
        .where(
            InterviewSession.user_id == user_id,
            InterviewSession.deleted_at.is_(None),
        )
    )

    if interview_type:
        base_query = base_query.where(InterviewSession.interview_type == interview_type)

    count_result = await db.execute(
        select(func.count()).select_from(base_query.subquery())
    )
    total = count_result.scalar_one()

    offset = (page - 1) * limit
    paginated_query = (
        base_query
        .options(selectinload(InterviewSession.responses))
        .order_by(InterviewSession.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(paginated_query)
    sessions = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "sessions": [
            {
                "session_id": s.id,
                "interview_type": s.interview_type,
                "status": s.status,
                "date": s.created_at,
                "started_at": s.started_at,
                "ended_at": s.ended_at,
                "duration_mins": s.duration_mins,
                "questions_count": len(s.responses),
                "overall_score": s.overall_score,
                "improvement_delta": s.improvement_delta,
                "has_recordings": any(r.audio_url for r in s.responses),
            }
            for s in sessions
        ],
    }


# ── Replay ────────────────────────────────────────────────────────────────────

async def get_session_result(db: AsyncSession, session_id: UUID) -> dict:
    """
    Full replay data for a completed session.
    Returns all question-by-question breakdown ordered by question_index.
    """
    session_result = await db.execute(
        select(InterviewSession).where(InterviewSession.id == session_id)
    )
    session = session_result.scalar_one_or_none()
    if not session:
        return {"error": "Session not found."}
    if session.status != "completed":
        return {"error": "Session is still active. Complete the interview first."}

    responses_result = await db.execute(
        select(UserResponse, Question)
        .join(Question, UserResponse.question_id == Question.id)
        .where(UserResponse.session_id == session_id)
        .order_by(
            UserResponse.question_index.asc().nullslast(),
            UserResponse.created_at.asc(),
        )
    )

    responses = [
        {
            "question_index": row.UserResponse.question_index,
            "question_text": row.Question.text,
            "difficulty": row.Question.difficulty,
            "user_answer": row.UserResponse.user_answer,
            "is_correct": row.UserResponse.is_correct,
            "feedback": row.UserResponse.feedback,
            "confidence_score": row.UserResponse.confidence_score,
            "audio_url": row.UserResponse.audio_url,
            "answered_at": row.UserResponse.answered_at,
            "time_taken_sec": row.UserResponse.time_taken_sec,
        }
        for row in responses_result.all()
    ]

    return {
        "session_id": session.id,
        "interview_type": session.interview_type,
        "status": session.status,
        "started_at": session.started_at,
        "ended_at": session.ended_at,
        "duration_mins": session.duration_mins,
        "overall_score": session.overall_score,
        "improvement_delta": session.improvement_delta,
        "gap_analysis": session.feedback,
        "responses": responses,
    }


# ── Improvement History (progress chart) ──────────────────────────────────────

async def get_improvement_history(db: AsyncSession, user_id: str) -> dict:
    """
    Returns all completed sessions in chronological order for progress chart.
    """
    stmt = (
        select(InterviewSession)
        .where(
            InterviewSession.user_id == user_id,
            InterviewSession.status == "completed",
            InterviewSession.deleted_at.is_(None),
        )
        .order_by(InterviewSession.created_at.asc())
    )
    result = await db.execute(stmt)
    sessions = result.scalars().all()

    scores = [s.overall_score for s in sessions if s.overall_score is not None]

    return {
        "user_id": user_id,
        "total_sessions": len(sessions),
        "average_score": round(sum(scores) / len(scores), 2) if scores else None,
        "best_score": max(scores) if scores else None,
        "sessions": [
            {
                "session_id": s.id,
                "interview_type": s.interview_type,
                "date": s.created_at,
                "overall_score": s.overall_score,
                "improvement_delta": s.improvement_delta,
                "duration_mins": s.duration_mins,
            }
            for s in sessions
        ],
    }