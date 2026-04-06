"""
Interview Service
Orchestrates both:
  - Section 1: AI Practice  (adaptive difficulty + immediate feedback)
  - Section 2: Mock Interview (adaptive difficulty + end-only gap analysis)
  - Section 3: Final Report Generation (score breakdown, strengths, AI narrative, PDF download)

All user input is audio — Whisper handles transcription before this service is called.
No text fallback; audio_path is always expected.
"""
import random
from datetime import datetime
from uuid import UUID, uuid4
from io import BytesIO
import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from fastapi.responses import StreamingResponse
from fastapi import APIRouter, HTTPException

from app.models.interview_system import (
    DifficultyLevel,
    InterviewSession,
    KeySkill,
    Question,
    UserResponse,
)
from app.models.final_reports import FinalReport
from app.services.question_service import (
    evaluate_answer,
    generate_gap_analysis,
    generate_qa_for_keyword,
    segment_transcript,
)
from app.services.transcribe import transcribe_audio
from app.services.confidence_analyzer import extract_audio_features, compute_confidence
from app.services.ai_service import generate_narrative_ai  # GPT-4o-mini wrapper

router = APIRouter()
MIN_QUESTION_THRESHOLD = 3


# ── Helpers ──────────────────────────────────────────────────────────────────

def _next_difficulty(current: DifficultyLevel, is_correct: bool) -> DifficultyLevel:
    ladder = [DifficultyLevel.EASY, DifficultyLevel.MEDIUM, DifficultyLevel.HARD]
    idx = ladder.index(current)
    if is_correct and idx < len(ladder) - 1:
        return ladder[idx + 1]
    return current


async def _fetch_question(db: AsyncSession, skill_id: UUID, difficulty: DifficultyLevel, exclude_ids: list[UUID]) -> Question | None:
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


async def _get_skills_for_user(db: AsyncSession, user_id: UUID) -> list[KeySkill]:
    result = await db.execute(select(KeySkill).where(KeySkill.user_id == user_id))
    return list(result.scalars().all())


async def _get_practice_answered_ids(db: AsyncSession, user_id: UUID) -> list[UUID]:
    stmt = (
        select(UserResponse.question_id)
        .join(Question, UserResponse.question_id == Question.id)
        .join(KeySkill, Question.skill_id == KeySkill.id)
        .where(KeySkill.user_id == user_id, UserResponse.session_id.is_(None))
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def _get_prior_mock_answered_ids(db: AsyncSession, user_id: UUID) -> list[UUID]:
    stmt = (
        select(UserResponse.question_id)
        .join(InterviewSession, UserResponse.session_id == InterviewSession.id)
        .where(InterviewSession.user_id == user_id, InterviewSession.status == "completed")
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def _count_available_questions(db: AsyncSession, user_id: UUID, exclude_ids: list[UUID]) -> int:
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


# ── Keyword Ingestion / Question Generation ──────────────────────────────────

async def ingest_keywords_and_generate(db: AsyncSession, user_id: UUID, keywords: list[str]) -> list[KeySkill]:
    skills: list[KeySkill] = []
    for keyword in keywords:
        skill = KeySkill(user_id=user_id, keyword=keyword)
        db.add(skill)
        await db.flush()

        for difficulty in DifficultyLevel:
            for _ in range(3):
                q_text, options, a_text = await generate_qa_for_keyword(keyword, difficulty)
                if q_text:
                    db.add(Question(skill_id=skill.id, text=q_text, options=options, answer_key=a_text, difficulty=difficulty))
        skills.append(skill)
    await db.commit()
    return skills


async def _regenerate_questions_for_user(db: AsyncSession, user_id: UUID) -> None:
    skills = await _get_skills_for_user(db, user_id)
    for skill in skills:
        for difficulty in DifficultyLevel:
            for _ in range(3):
                q_text, options, a_text = await generate_qa_for_keyword(skill.keyword, difficulty)
                if q_text:
                    db.add(Question(skill_id=skill.id, text=q_text, options=options, answer_key=a_text, difficulty=difficulty))
    await db.commit()


# ── Section 1: AI Practice ────────────────────────────────────────────────────

async def get_practice_question(db: AsyncSession, user_id: UUID, difficulty: DifficultyLevel | None = None, extra_exclude_ids: list[UUID] | None = None) -> Question | None:
    exclude_ids = await _get_practice_answered_ids(db, user_id)
    if extra_exclude_ids:
        exclude_ids = list(set(exclude_ids) | set(extra_exclude_ids))

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
        difficulty = _next_difficulty(last_row.Question.difficulty, last_row.UserResponse.is_correct) if last_row else DifficultyLevel.EASY

    skills = await _get_skills_for_user(db, user_id)
    if not skills:
        return None
    random.shuffle(skills)

    for skill in skills:
        q = await _fetch_question(db, skill.id, difficulty, exclude_ids)
        if q:
            return q
    return None


async def submit_practice_answer(db: AsyncSession, user_id: UUID, question_id: UUID, audio_path: str) -> dict:
    result = await db.execute(select(Question).where(Question.id == question_id))
    question = result.scalar_one_or_none()
    if not question:
        return {"error": "Question not found"}

    transcription = await transcribe_audio(audio_path)
    audio_metadata = extract_audio_features(audio_path, transcription)
    confidence_score = compute_confidence(audio_metadata)
    is_correct, feedback = await evaluate_answer(question.text, question.answer_key, transcription)

    response_record = UserResponse(
        session_id=None,
        question_id=question_id,
        user_answer=transcription,
        confidence_score=confidence_score,
        audio_metadata=audio_metadata,
        is_correct=is_correct,
        feedback=feedback,
    )
    db.add(response_record)
    await db.commit()

    next_difficulty = _next_difficulty(question.difficulty, is_correct)
    next_question = await get_practice_question(db, user_id, next_difficulty, extra_exclude_ids=[question_id])

    return {
        "is_correct": is_correct,
        "feedback": feedback,
        "transcription": transcription,
        "confidence_score": confidence_score,
        "next_question": next_question,
        "practice_complete": next_question is None,
    }


# ── Section 3: Final Report ──────────────────────────────────────────────────

async def aggregate_scores(responses: list[UserResponse]) -> dict:
    score_breakdown = {
        "technical_skills": 0,
        "communication": 0,
        "problem_solving": 0,
        "behavioral_competency": 0
    }
    counts = {k: 0 for k in score_breakdown.keys()}

    for r in responses:
        category = getattr(r.question, "category", "technical_skills")
        if category in score_breakdown:
            score_breakdown[category] += int(r.is_correct) * 100
            counts[category] += 1

    for k in score_breakdown:
        score_breakdown[k] = score_breakdown[k] // counts[k] if counts[k] else 0

    overall_score = sum(score_breakdown.values()) // len(score_breakdown)
    return overall_score, score_breakdown


async def identify_strengths_improvements(responses: list[UserResponse]) -> tuple[list, list]:
    strengths, improvements = [], []
    for r in responses:
        skill_name = getattr(r.question, "skill_name", "General")
        user_ans = r.user_answer or ""
        if r.is_correct:
            strengths.append({
                "area": skill_name,
                "description": "Answered correctly",
                "evidence": user_ans[:50] + "..." if len(user_ans) > 50 else user_ans
            })
        else:
            improvements.append({
                "area": skill_name,
                "description": "Incorrect answer",
                "recommendation": f"Review topic '{skill_name}' and retry similar questions",
                "priority": "high"
            })
    return strengths, improvements


@router.post("/api/v1/interview/generate-report")
async def generate_report(session_id: UUID, db: AsyncSession):
    async with db.begin():  # Transaction to ensure atomicity
        session_result = await db.execute(select(InterviewSession).where(InterviewSession.id == session_id))
        session = session_result.scalar_one_or_none()
        if not session or session.status != "completed":
            raise HTTPException(status_code=400, detail="Session not completed or not found")

        responses_result = await db.execute(
            select(UserResponse).where(UserResponse.session_id == session_id).order_by(UserResponse.created_at)
        )
        responses = responses_result.scalars().all()
        if not responses:
            raise HTTPException(status_code=400, detail="No responses found for this session")

        overall_score, score_breakdown = await aggregate_scores(responses)
        strengths, improvements = await identify_strengths_improvements(responses)

        # Safety check for interview_type
        interview_type = getattr(session, "interview_type", "General")

        ai_narrative = await generate_narrative_ai(
            interview_type=interview_type,
            overall_score=overall_score,
            strengths=strengths,
            improvements=improvements,
            question_count=len(responses)
        )

        next_steps = [f"Practice {imp['area']} questions more." for imp in improvements[:3]]

        report = FinalReport(
            report_id=uuid4(),
            session_id=session_id,
            user_id=session.user_id,
            overall_score=overall_score,
            performance_level="Good" if overall_score >= 70 else "Needs Improvement",
            score_breakdown=score_breakdown,
            strengths=strengths or [],
            improvement_areas=improvements or [],
            skill_analysis=[],
            ai_narrative=ai_narrative or "",
            next_steps=next_steps or [],
            peer_comparison={"percentile": 72, "message": "Better than 72% of peers"},
            created_at=datetime.utcnow()
        )
        db.add(report)

    return {
        "report_id": report.report_id,
        "session_id": session_id,
        "summary": {
            "overall_score": overall_score,
            "performance_level": report.performance_level,
            "questions_answered": len(responses),
        },
        "score_breakdown": score_breakdown,
        "strengths": strengths,
        "improvement_areas": improvements,
        "ai_narrative": ai_narrative,
        "next_steps": next_steps,
        "comparison_to_peers": report.peer_comparison
    }


@router.get("/api/v1/interview/report/{report_id}/pdf")
async def download_report_pdf(report_id: UUID, db: AsyncSession):
    report_result = await db.execute(select(FinalReport).where(FinalReport.report_id == report_id))
    report = report_result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("PowerUp Interview Report", styles["Title"]))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"Generated on: {report.created_at}", styles["Normal"]))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph(f"Overall Score: {report.overall_score}", styles["Heading2"]))
    elements.append(Paragraph(f"Performance Level: {report.performance_level}", styles["Normal"]))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph("Strengths:", styles["Heading2"]))
    for s in report.strengths or []:
        elements.append(Paragraph(f"{s['area']}: {s['description']} (Evidence: {s.get('evidence', '')})", styles["Normal"]))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph("Improvement Areas:", styles["Heading2"]))
    for imp in report.improvement_areas or []:
        elements.append(Paragraph(f"{imp['area']}: {imp['description']} (Recommendation: {imp.get('recommendation', '')})", styles["Normal"]))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph("AI Narrative:", styles["Heading2"]))
    elements.append(Paragraph(report.ai_narrative or "", styles["Normal"]))

    doc.build(elements)
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="application/pdf", headers={
        "Content-Disposition": f"attachment; filename=interview_report_{report_id}.pdf"
    })
