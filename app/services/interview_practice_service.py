"""
Interview Practice Service — Section 1: AI Practice flow.
Handles keyword ingestion, question generation, and practice answer evaluation.
"""

import logging
import random
from datetime import datetime
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.interview_system import (
    DifficultyLevel,
    KeySkill,
    Question,
    UserResponse,
)
from app.services.confidence_analyzer import compute_confidence, extract_audio_features
from app.services.interview_helpers import (
    fetch_question,
    get_skills_for_user,
    next_difficulty,
    question_to_dict,
    safe_dict,
    safe_pronunciation,
)
from app.services.pronunciation_analyzer import analyze_pronunciation
from app.services.question_service import (
    evaluate_answer,
    generate_qa_for_keyword,
)
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


async def regenerate_questions(db: AsyncSession, user_id: str) -> None:
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
