"""
Interview Service — Sprint 2 Task 2 (Final Working)
"""
import random
from datetime import datetime
from uuid import UUID

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import noload

from app.models.interview_system import (
    DifficultyLevel,
    InterviewSession,
    KeySkill,
    Question,
    UserResponse,
)
from app.models.analytics_models import (
    SessionAnalytics,
    UserMilestone,
    SkillScoreHistory,
)
from app.services.question_service import (
    evaluate_answer,
    generate_gap_analysis,
    generate_qa_for_keyword,
)
from app.services.transcribe import transcribe_audio
from app.services.confidence_analyzer import extract_audio_features, compute_confidence
from app.services.pronunciation_analyzer import analyze_pronunciation


# ── Helpers ───────────────────────────────────────────────────────────────────

def _performance_level(score: int | None) -> str:
    if score is None:
        return "N/A"
    if score >= 90:
        return "Excellent"
    if score >= 75:
        return "Good"
    if score >= 60:
        return "Satisfactory"
    if score >= 40:
        return "Needs Improvement"
    return "Poor"


def _safe_dict(value) -> dict | None:
    """Return dict or None — never a string 'null'."""
    if isinstance(value, dict):
        return value
    return None


def _safe_pronunciation(result) -> dict:
    """Ensure pronunciation result is always JSON serializable."""
    if not isinstance(result, dict):
        return {
            "phoneme_score": None,
            "fluency_score": None,
            "mistakes": [],
            "tips": [],
            
        }
    return {
        "phoneme_score": result.get("phoneme_score") if isinstance(result.get("phoneme_score"), (int, float, type(None))) else None,
        "fluency_score": result.get("fluency_score") if isinstance(result.get("fluency_score"), (int, float, type(None))) else None,
        "mistakes": result.get("mistakes") if isinstance(result.get("mistakes"), list) else [],
        "tips": result.get("tips") if isinstance(result.get("tips"), list) else [],
        "ref_ipa": str(result.get("ref_ipa")) if result.get("ref_ipa") else None,
        "user_ipa": str(result.get("user_ipa")) if result.get("user_ipa") else None,
    }


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


def _question_to_dict(q: Question) -> dict:
    """Convert SQLAlchemy Question to plain dict."""
    return {
        "id": str(q.id),
        "text": q.text,
        "difficulty": q.difficulty,
        "skill_id": str(q.skill_id),
    }


# ── Session Analytics Service ─────────────────────────────────────────────────

class SessionAnalyticsService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create(self, user_id: str) -> SessionAnalytics:
        result = await self.db.execute(
            select(SessionAnalytics).where(SessionAnalytics.user_id == user_id)
        )
        analytics = result.scalar_one_or_none()
        if not analytics:
            analytics = SessionAnalytics(user_id=user_id)
            self.db.add(analytics)
            await self.db.flush()
        return analytics

    async def update(self, user_id: str, session: InterviewSession) -> None:
        analytics = await self.get_or_create(user_id)
        analytics.total_sessions += 1
        analytics.total_time_mins += session.duration_mins or 0
        analytics.last_session_at = session.ended_at

        if session.overall_score is not None:
            if analytics.avg_score is None:
                analytics.avg_score = session.overall_score
            else:
                total = float(analytics.avg_score) * (analytics.total_sessions - 1)
                analytics.avg_score = round(
                    (total + session.overall_score) / analytics.total_sessions, 2
                )
            if analytics.best_score is None or session.overall_score > analytics.best_score:
                analytics.best_score = session.overall_score
            if analytics.worst_score is None or session.overall_score < analytics.worst_score:
                analytics.worst_score = session.overall_score

        type_count_result = await self.db.execute(
            select(InterviewSession.interview_type, func.count(InterviewSession.id).label("cnt"))
            .where(
                InterviewSession.user_id == user_id,
                InterviewSession.status == "completed",
                InterviewSession.deleted_at.is_(None),
            )
            .group_by(InterviewSession.interview_type)
            .order_by(desc("cnt"))
            .limit(1)
        )
        top_type = type_count_result.first()
        if top_type:
            analytics.most_practiced_type = top_type[0]

        analytics.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.check_milestones(user_id, session, analytics.total_sessions)

    async def check_milestones(
        self, user_id: str, session: InterviewSession, total_count: int
    ) -> None:
        milestones_to_check = [
            ("first_interview", "First Interview", lambda s, c: c == 1),
            ("score_70", "Score Above 70", lambda s, c: (s.overall_score or 0) >= 70),
            ("score_80", "Score Above 80", lambda s, c: (s.overall_score or 0) >= 80),
            ("score_90", "Score Above 90", lambda s, c: (s.overall_score or 0) >= 90),
            ("5_interviews", "5 Interviews Completed", lambda s, c: c >= 5),
            ("10_interviews", "10 Interviews Completed", lambda s, c: c >= 10),
            ("25_interviews", "25 Interviews Completed", lambda s, c: c >= 25),
        ]
        for m_type, m_name, condition in milestones_to_check:
            if not condition(session, total_count):
                continue
            existing = await self.db.execute(
                select(UserMilestone).where(
                    UserMilestone.user_id == user_id,
                    UserMilestone.milestone_type == m_type,
                )
            )
            if existing.scalar_one_or_none():
                continue
            self.db.add(UserMilestone(
                user_id=user_id,
                milestone_type=m_type,
                milestone_name=m_name,
                achieved_at=datetime.utcnow(),
                session_id=session.id,
            ))
        await self.db.commit()

    async def save_skill_scores(
        self, user_id: str, session_id: UUID, skills: list[KeySkill], overall_score: int
    ) -> None:
        for skill in skills:
            self.db.add(SkillScoreHistory(
                user_id=user_id,
                skill_name=skill.keyword,
                score=overall_score,
                session_id=session_id,
                recorded_at=datetime.utcnow(),
            ))
        await self.db.commit()


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
    user_answer = None
    pronunciation_result = {}

    if audio_path:
        transcription = await transcribe_audio(audio_path)
        audio_metadata = _safe_dict(extract_audio_features(audio_path, transcription))
        confidence_score = compute_confidence(audio_metadata) if audio_metadata else None
        user_answer = transcription
        pronunciation_result = await analyze_pronunciation(question.text, transcription)

    if not user_answer:
        return {"error": "No answer provided."}

    is_correct, feedback = await evaluate_answer(question.text, question.answer_key, user_answer)

    response_record = UserResponse(
        session_id=None,
        question_id=question_id,
        user_answer=user_answer,
        confidence_score=confidence_score,
        audio_metadata=audio_metadata,
        is_correct=is_correct,
        feedback=feedback,
        answered_at=datetime.utcnow(),
        pronunciation_score=_safe_pronunciation(pronunciation_result).get("phoneme_score"),
        pronunciation_data=_safe_dict(_safe_pronunciation(pronunciation_result)),
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
        "pronunciation": _safe_pronunciation(pronunciation_result),
        "next_question": _question_to_dict(next_question) if next_question else None,
        "practice_complete": next_question is None,
    }


# ── Section 2: Mock Interview ─────────────────────────────────────────────────

async def start_interview_session(db: AsyncSession, user_id: str) -> dict:
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

    if not first_question:
        return {"error": "No questions available."}

    session.feedback = str(first_question.id)
    await db.commit()

    return {"session": session, "current_question": first_question}


async def submit_batch_answer(
    db: AsyncSession,
    session_id: UUID,
    audio_path: str | None = None,
    user_answer: str | None = None,
) -> dict:
    result = await db.execute(
        select(InterviewSession)
        .where(InterviewSession.id == session_id)
        .options(noload("*"))
    )
    session = result.scalar_one_or_none()
    if not session or session.status != "active":
        return {"error": "Session not found or already completed."}

    count_result = await db.execute(
        select(func.count(UserResponse.id))
        .where(UserResponse.session_id == session_id)
    )
    response_count = count_result.scalar_one()

    answered_result = await db.execute(
        select(UserResponse.question_id)
        .where(UserResponse.session_id == session_id)
    )
    answered_ids = list(answered_result.scalars().all())

    current_q_id_str = session.feedback
    if not current_q_id_str or len(current_q_id_str) != 36:
        return {"error": "No active question found for this session."}

    current_q_id = UUID(current_q_id_str)
    q_result = await db.execute(select(Question).where(Question.id == current_q_id))
    current_question = q_result.scalar_one_or_none()
    if not current_question:
        return {"error": "Question not found."}

    transcription = None
    confidence_score = None
    audio_metadata = None
    pronunciation_result = {}

    if audio_path:
        transcription = await transcribe_audio(audio_path)
        audio_metadata = _safe_dict(extract_audio_features(audio_path, transcription))
        confidence_score = compute_confidence(audio_metadata) if audio_metadata else None
        user_answer = transcription
        pronunciation_result = await analyze_pronunciation(
            reference_text=current_question.text,
            transcript=transcription,
        )

    if not user_answer:
        return {"error": "No answer provided (neither text nor audio)."}

    is_correct, feedback = await evaluate_answer(
        current_question.text, current_question.answer_key, user_answer
    )

    safe_p = _safe_pronunciation(pronunciation_result)

    response_record = UserResponse(
        session_id=session_id,
        question_id=current_q_id,
        user_answer=user_answer,
        confidence_score=confidence_score,
        audio_metadata=audio_metadata,          # ← always dict or None
        is_correct=is_correct,
        feedback=None,
        question_index=response_count,
        answered_at=datetime.utcnow(),
        pronunciation_score=safe_p.get("phoneme_score"),
        pronunciation_data=safe_p if any(v is not None for v in safe_p.values()) else None,
    )
    db.add(response_record)
    await db.commit()

    next_difficulty = _next_difficulty(current_question.difficulty, is_correct)
    answered_ids = answered_ids + [current_q_id]

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
            "next_question": _question_to_dict(next_question),
            "transcription": transcription,
            "confidence_score": confidence_score,
            "pronunciation": safe_p,
        }

    # ── Session complete ──────────────────────────────────────────
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

    analytics_svc = SessionAnalyticsService(db)
    await analytics_svc.update(session.user_id, session)
    skills = await _get_skills_for_user(db, session.user_id)
    await analytics_svc.save_skill_scores(session.user_id, session_id, skills, overall_score)

    return {
        "session_complete": True,
        "next_question": None,
        "transcription": transcription,
        "confidence_score": confidence_score,
        "pronunciation": safe_p,
    }


async def get_session_feedback(db: AsyncSession, session_id: UUID) -> dict:
    result = await db.execute(
        select(InterviewSession).where(InterviewSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        return {"error": "Session not found."}
    if session.status != "completed":
        return {"error": "Session is still active. Complete the interview first."}
    return {"session_id": session_id, "feedback": session.feedback}


# ── History ───────────────────────────────────────────────────────────────────

async def get_user_sessions(
    db: AsyncSession,
    user_id: str,
    page: int = 1,
    limit: int = 10,
    interview_type: str | None = None,
    sort: str = "date_desc",
) -> dict:
    base_query = (
        select(InterviewSession)
        .where(
            InterviewSession.user_id == user_id,
            InterviewSession.deleted_at.is_(None),
        )
    )

    if interview_type:
        base_query = base_query.where(InterviewSession.interview_type == interview_type)

    sort_map = {
        "date_desc": InterviewSession.created_at.desc(),
        "date_asc": InterviewSession.created_at.asc(),
        "score_desc": InterviewSession.overall_score.desc(),
        "score_asc": InterviewSession.overall_score.asc(),
    }
    base_query = base_query.order_by(sort_map.get(sort, InterviewSession.created_at.desc()))

    count_result = await db.execute(
        select(func.count()).select_from(base_query.subquery())
    )
    total = count_result.scalar_one()

    offset = (page - 1) * limit
    result = await db.execute(base_query.offset(offset).limit(limit))
    sessions = result.scalars().all()

    session_list = []
    for s in sessions:
        rc = await db.execute(
            select(func.count(UserResponse.id))
            .where(UserResponse.session_id == s.id)
        )
        q_count = rc.scalar_one()

        rec = await db.execute(
            select(func.count(UserResponse.id))
            .where(
                UserResponse.session_id == s.id,
                UserResponse.audio_url.isnot(None),
            )
        )
        has_recordings = rec.scalar_one() > 0

        skills_result = await db.execute(
            select(KeySkill.keyword)
            .join(Question, Question.skill_id == KeySkill.id)
            .join(UserResponse, UserResponse.question_id == Question.id)
            .where(UserResponse.session_id == s.id)
            .distinct()
        )
        key_skills = list(skills_result.scalars().all())

        session_list.append({
            "session_id": s.id,
            "interview_type": s.interview_type,
            "status": s.status,
            "date": s.created_at,
            "started_at": s.started_at,
            "ended_at": s.ended_at,
            "duration_mins": s.duration_mins,
            "questions_count": q_count,
            "overall_score": s.overall_score,
            "performance_level": _performance_level(s.overall_score),
            "improvement_delta": s.improvement_delta,
            "has_recordings": has_recordings,
            "has_report": s.feedback is not None and s.status == "completed",
            "key_skills_tested": key_skills,
        })

    scores = [s["overall_score"] for s in session_list if s["overall_score"] is not None and s["status"] == "completed"]


    last5_result = await db.execute(
        select(InterviewSession.overall_score)
        .where(
            InterviewSession.user_id == user_id,
            InterviewSession.status == "completed",
            InterviewSession.overall_score.isnot(None),
            InterviewSession.deleted_at.is_(None),
        )
        .order_by(InterviewSession.created_at.desc())
        .limit(5)
    )
    last5 = list(last5_result.scalars().all())
    improvement_trend = None
    if len(last5) >= 2:
        delta = last5[0] - last5[-1]
        sign = "+" if delta >= 0 else ""
        improvement_trend = f"{sign}{delta}% over last {len(last5)} interviews"

    type_result = await db.execute(
        select(InterviewSession.interview_type, func.count(InterviewSession.id).label("cnt"))
        .where(
            InterviewSession.user_id == user_id,
            InterviewSession.deleted_at.is_(None),
        )
        .group_by(InterviewSession.interview_type)
        .order_by(desc("cnt"))
        .limit(1)
    )
    top_type_row = type_result.first()
    most_practiced_type = top_type_row[0] if top_type_row else None

    summary = {
        "total_interviews": total,
        "avg_score": round(sum(scores) / len(scores), 2) if scores else None,
        "improvement_trend": improvement_trend,
        "most_practiced_type": most_practiced_type,
        "total_time_mins": sum([s["duration_mins"] or 0 for s in session_list]),
    }

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "sessions": session_list,
        "summary": summary,
    }


# ── Replay ────────────────────────────────────────────────────────────────────

async def get_session_result(db: AsyncSession, session_id: UUID) -> dict:
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
    rows = responses_result.all()

    questions = []
    for i, row in enumerate(rows):
        ur = row.UserResponse
        q = row.Question

        skill_result = await db.execute(
            select(KeySkill.keyword).where(KeySkill.id == q.skill_id)
        )
        skill_keyword = skill_result.scalar_one_or_none()
        skill_tags = [skill_keyword] if skill_keyword else []

        p_data = ur.pronunciation_data or {}
        mistakes = p_data.get("mistakes", []) if isinstance(p_data.get("mistakes"), list) else []
        mispronounced = [
            m.get("expected", "") for m in mistakes
            if isinstance(m, dict) and m.get("type") in ("wrong", "missing")
            and m.get("expected")
            ]
            
        user_answer = ur.user_answer or ""
        filler_words = ["um", "uh", "like", "so", "you know", "actually", "erm"]
        filler_count = sum(
            user_answer.lower().count(f) for f in filler_words
            )

        questions.append({
            "question_id": str(q.id),
            "question_number": i + 1,
            "question_text": q.text,
            "difficulty": q.difficulty,
            "skill_tags": skill_tags,
            "response": {
                "user_answer": ur.user_answer,
                "response_time_secs": ur.time_taken_sec,
                "audio_url": ur.audio_url,
            },
            "evaluation": {
                "score": ur.confidence_score,
                "is_correct": ur.is_correct,
                "feedback": ur.feedback,
                "model_answer": q.answer_key,
            },
            "pronunciation": {
                "score": ur.pronunciation_score,
                "mispronounced_words": mispronounced,
                "filler_count": filler_count,
                "tips": p_data.get("tips", []) if isinstance(p_data.get("tips"), list) else [],
                "fluency_score": p_data.get("fluency_score"),
            },
        })
    
    gap = session.feedback or ""
    strengths = []
    improvements = []
    current_section = None
    for line in gap.split("\n"):
        line = line.strip()
        if not line:
            continue
        line_upper = line.upper()
        if "STRENGTH" in line_upper:
            current_section = "strengths"
            continue
        elif any(k in line_upper for k in ["WEAKNESS", "IMPROVEMENT", "RECOMMENDATION"]):
            current_section = "improvements"
            continue
        if ":**" in line or line.startswith("#"):
            continue
        if line.startswith(("- ", "* ")) or (len(line) > 2 and line[0].isdigit() and line[1] in ".)"):
            clean = line.lstrip("0123456789.-*) ").replace("**", "").strip()
            if not clean or len(clean) < 5:
                continue
            if current_section == "strengths" and len(strengths) < 3:
                strengths.append(clean)
            elif current_section == "improvements" and len(improvements) < 3:
                improvements.append(clean)

    return {
        "session_id": str(session.id),
        "user_id": session.user_id,
        "interview_type": session.interview_type,
        "status": session.status,
        "started_at": session.started_at,
        "ended_at": session.ended_at,
        "duration_mins": session.duration_mins,
        "overall_score": session.overall_score,
        "improvement_delta": session.improvement_delta,
        "gap_analysis": session.feedback,
        "questions": questions,
        
        "report_summary": {
            "strengths": strengths,
            "improvements": improvements,
        },
    }


# ── Progress ──────────────────────────────────────────────────────────────────

async def get_improvement_history(db: AsyncSession, user_id: str) -> dict:
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

    score_progression = [
        {
            "date": s.created_at.strftime("%Y-%m-%d"),
            "score": s.overall_score,
            "type": s.interview_type,
        }
        for s in sessions
        if s.overall_score is not None
    ]

    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    interviews_this_month = sum(1 for s in sessions if s.created_at >= month_start)

    skill_result = await db.execute(
        select(SkillScoreHistory)
        .where(SkillScoreHistory.user_id == user_id)
        .order_by(SkillScoreHistory.recorded_at.asc())
    )
    skill_rows = skill_result.scalars().all()

    skill_map: dict[str, list[int]] = {}
    for row in skill_rows:
        if row.skill_name and row.score is not None:
            skill_map.setdefault(row.skill_name, []).append(row.score)

    skill_improvement = [
        {
            "skill": skill,
            "initial_score": scores_list[0],
            "current_score": scores_list[-1],
            "change": f"+{scores_list[-1] - scores_list[0]}"
            if scores_list[-1] >= scores_list[0]
            else str(scores_list[-1] - scores_list[0]),
        }
        for skill, scores_list in skill_map.items()
    ]

    streak = 0
    longest_gap = 0
    total_weeks = 0
    if sessions:
        today = now.date()
        prev_date = today
        for s in reversed(sessions):
            s_date = s.created_at.date()
            gap = (prev_date - s_date).days
            if gap <= 1:
                streak += 1
                prev_date = s_date
            else:
                break

        dates = [s.created_at for s in sessions]
        for i in range(1, len(dates)):
            gap_days = (dates[i] - dates[i - 1]).days
            if gap_days > longest_gap:
                longest_gap = gap_days

        if len(sessions) >= 2:
            total_days = (sessions[-1].created_at - sessions[0].created_at).days or 1
            total_weeks = max(1, total_days / 7)

    avg_per_week = round(len(sessions) / total_weeks, 1) if total_weeks > 0 else len(sessions)

    milestones_result = await db.execute(
        select(UserMilestone)
        .where(UserMilestone.user_id == user_id)
        .order_by(UserMilestone.achieved_at.asc())
    )
    milestones = [
        {
            "name": m.milestone_name,
            "achieved_at": m.achieved_at.strftime("%Y-%m-%d"),
        }
        for m in milestones_result.scalars().all()
    ]

    return {
        "user_id": user_id,
        "total_interviews": len(sessions),
        "interviews_this_month": interviews_this_month,
        "score_progression": score_progression,
        "skill_improvement": skill_improvement,
        "consistency": {
            "avg_interviews_per_week": avg_per_week,
            "longest_gap_days": longest_gap,
            "current_streak": streak,
        },
        "milestones": milestones,
        "average_score": round(sum(scores) / len(scores), 2) if scores else None,
        "best_score": max(scores) if scores else None,
    }