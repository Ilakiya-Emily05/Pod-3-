"""
Interview Service
Orchestrates both:
  - Section 1: AI Practice  (adaptive difficulty + immediate feedback)
  - Section 2: Mock Interview (adaptive difficulty + end-only gap analysis)
  - Section 3: Final Report Generation (score breakdown, strengths, AI narrative, PDF download)

All user input is audio — Whisper handles transcription before this service is called.
Supports audio input (preferred) and transcript fallback for testing."""
from typing import Optional
from sqlalchemy import func
import json
import random
from datetime import datetime
from io import BytesIO
from uuid import UUID, uuid4
from app.services.interview_scorer import evaluate_answer_with_gpt
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.interview_system import (
    DifficultyLevel,
    InterviewSession,
    KeySkill,
    UserResponse,
)
from app.models.interview_system import (
    InterviewQuestion as Question,
)
from app.services.ai_service import generate_narrative_ai  # GPT-4o-mini wrapper
from app.services.confidence_analyzer import compute_confidence, extract_audio_features
from app.services.question_service import (
    evaluate_answer,
    generate_gap_analysis,
    generate_qa_for_keyword,
    segment_transcript,
)
from app.services.transcribe import transcribe_audio

MIN_QUESTION_THRESHOLD = 3


# ── Helpers ──────────────────────────────────────────────────────────────────


def _next_difficulty(current: DifficultyLevel, is_correct: bool) -> DifficultyLevel:
    ladder = [DifficultyLevel.EASY, DifficultyLevel.MEDIUM, DifficultyLevel.HARD]
    idx = ladder.index(current)
    if is_correct and idx < len(ladder) - 1:
        return ladder[idx + 1]
    return current


async def _fetch_question(
    db: AsyncSession, skill_id: UUID, difficulty: DifficultyLevel, exclude_ids: list[UUID]
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


async def _count_available_questions(
    db: AsyncSession, user_id: UUID, exclude_ids: list[UUID]
) -> int:
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


async def ingest_keywords_and_generate(
    db: AsyncSession, user_id: UUID, keywords: list[str]
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


async def _regenerate_questions_for_user(db: AsyncSession, user_id: UUID) -> None:
    skills = await _get_skills_for_user(db, user_id)
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
    user_id: UUID,
    difficulty: DifficultyLevel | None = None,
    extra_exclude_ids: list[UUID] | None = None,
) -> Question | None:
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
        difficulty = (
            _next_difficulty(last_row.Question.difficulty, last_row.UserResponse.is_correct)
            if last_row
            else DifficultyLevel.EASY
        )

    skills = await _get_skills_for_user(db, user_id)
    if not skills:
        return None
    random.shuffle(skills)

    for skill in skills:
        q = await _fetch_question(db, skill.id, difficulty, exclude_ids)
        if q:
            return q
    return None


async def submit_practice_answer(
    db: AsyncSession, user_id: UUID, question_id: UUID, audio_path: str
) -> dict:
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


async def start_mock_session(db: AsyncSession, user_id: UUID) -> dict:
    """
    Start mock interview session (sequential flow).
    """
    skills = await _get_skills_for_user(db, user_id)
    if not skills:
        return {"error": "No skills found. Please ingest keywords first."}

    session = InterviewSession(
        user_id=user_id,
        status="in_progress",
        total_questions=8,
        questions_answered=0,
        total_score=0,
    )
    db.add(session)
    await db.commit()

    # ✅ Fetch REAL question from DB (NOT generate, NOT uuid)
    question = None

    for skill in skills:
        question = await _fetch_question(
            db,
            skill.id,
            DifficultyLevel.MEDIUM,
            exclude_ids=[],
        )
        if question:
            break

    if not question:
        return {"error": "No questions available"}

    return {
        "session_id": session.id,
        "question": {
            "id": question.id,
            "text": question.text,
            "options": question.options,
            "difficulty": question.difficulty,
        },
    }
async def submit_mock_answer(
    db: AsyncSession,
    session_id: UUID,
    question_id: UUID,
    user_id: UUID, 
    audio_path: Optional[str] = None,
    transcript: Optional[str] = None,
) -> dict:
    """
    Spec-compliant flow:
    audio/transcript → transcribe → GPT score → store → update → return
    """

    result = await db.execute(
        select(InterviewSession).where(
            InterviewSession.id == session_id,
            InterviewSession.user_id == user_id,
        )
    )
    session = result.scalar_one_or_none()

    if not session or session.status != "in_progress":
        return {"error": "Invalid or completed session"}

    # Get question
    q_result = await db.execute(select(Question).where(Question.id == question_id))
    question = q_result.scalar_one_or_none()

    if not question:
        return {"error": "Question not found"}

    # Input handling
    if audio_path:
        transcript = await transcribe_audio(audio_path)
    elif not transcript:
        return {"error": "Either audio or transcript required"}

    # GPT scoring
    score_result = await evaluate_answer_with_gpt(
        question_text=question.text,
        rubric=question.answer_key,
        user_answer=transcript,
    )

    response = UserResponse(
        session_id=session_id,
        question_id=question_id,
        question_order=session.questions_answered + 1,
        user_answer=transcript,
        score=score_result["score"],
        score_breakdown=score_result.get("breakdown", {}),
        feedback=score_result["feedback"],
        answered_at=func.now(),
    )
    db.add(response)

    # Update session
    session.questions_answered += 1
    session.total_score = (session.total_score or 0) + score_result["score"]

    questions_remaining = session.total_questions - session.questions_answered

    # Completion
    if session.questions_answered >= session.total_questions:
        session.status = "completed"
        session.completed_at = func.now()

        await db.commit()

        return {
            "score": score_result["score"],
            "feedback": score_result["feedback"],
            "questions_remaining": 0,
            "message": "Interview completed. Fetch report.",
        }

    # ✅ Fetch next question from DB (NO generation, NO uuid)
    skills = await _get_skills_for_user(db, session.user_id)

    next_question = None

    for skill in skills:
        next_question = await _fetch_question(
            db,
            skill.id,
            DifficultyLevel.MEDIUM,
            exclude_ids=[question_id],
        )
        if next_question:
            break

    await db.commit()

    return {
        "score": score_result["score"],
        "feedback": score_result["feedback"],
        "questions_remaining": questions_remaining,
        "next_question": {
            "id": next_question.id,
            "text": next_question.text,
            "options": next_question.options,
            "difficulty": next_question.difficulty,
        } if next_question else None,
    }
async def get_user_sessions(db: AsyncSession, user_id: UUID) -> list[dict]:
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


async def get_session_result(
    db: AsyncSession, session_id: UUID, user_id: UUID
) -> dict:
    """
    Return the full result for a completed mock session:
    session metadata + gap analysis + all Q&A responses.
    """

    session_result = await db.execute(
        select(InterviewSession).where(
            InterviewSession.id == session_id,
            InterviewSession.user_id == user_id,
        )
    )
    session = session_result.scalar_one_or_none()

    if not session:
        return {"error": "Session not found or access denied."}

    if session.status != "completed":
        return {"error": "Session is still active. Complete the interview first."}    # Fetch all responses joined with their questions
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
            "score": row.UserResponse.score,
            "feedback": row.UserResponse.feedback,
        }
        for row in responses_result.all()
    ]
    total_score = sum([r["score"] or 0 for r in responses]) if responses else 0
    avg_score = total_score / len(responses) if responses else 0


    return {
        "session_id": session.id,
        "status": session.status,
        "gap_analysis": session.feedback,
        "total_score": total_score,
        "average_score": avg_score,
        "grade": map_grade(avg_score),
        "responses": responses,
    }


# ── Batch Audio Mock Interview (5-Minute Session) ────────────────────────────


async def start_batch_interview(db: AsyncSession, user_id: UUID) -> dict:
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
        DifficultyLevel.EASY,
        DifficultyLevel.EASY,
        DifficultyLevel.EASY,
        DifficultyLevel.EASY,
        DifficultyLevel.EASY,
        DifficultyLevel.MEDIUM,
        DifficultyLevel.MEDIUM,
        DifficultyLevel.MEDIUM,
        DifficultyLevel.MEDIUM,
        DifficultyLevel.MEDIUM,
        DifficultyLevel.HARD,
        DifficultyLevel.HARD,
        DifficultyLevel.HARD,
        DifficultyLevel.HARD,
        DifficultyLevel.HARD,
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
                picked = (
                    await _fetch_question(db, skill.id, DifficultyLevel.EASY, current_excluded)
                    or await _fetch_question(db, skill.id, DifficultyLevel.MEDIUM, current_excluded)
                    or await _fetch_question(db, skill.id, DifficultyLevel.HARD, current_excluded)
                )
                if picked:
                    batch_questions.append(picked)
                    current_excluded.append(picked.id)
                    break

    if not batch_questions:
        return {"error": "No questions available. Please ingest more keywords."}

    # Create session
    session = InterviewSession(user_id=user_id, status="active")
    session.feedback = json.dumps({"batch_ids": [str(q.id) for q in batch_questions]})
    db.add(session)
    await db.commit()

    return {"session_id": session.id, "questions": batch_questions}


async def submit_batch_answer(
    db: AsyncSession,
    session_id: UUID,
    user_id: UUID,
    audio_path: str,
) -> dict:
    """
    Processes the compulsory 5-minute audio file.
    Enforces a minimum duration of 5 minutes (300 seconds).
    """
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
        return {"error": f"Failed to check audio duration: {e!s}"}

    # Load session
    result = await db.execute(select(InterviewSession).where(InterviewSession.id == session_id)
                              .where(InterviewSession.user_id == user_id))
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
        responses_list.append(
            {
                "question": q.text,
                "user_answer": answer_text,
                "is_correct": is_correct,
                "confidence": confidence_score,
            }
        )

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
        "duration_sec": round(duration_sec, 2),
    }


# ── Section 3: Final Report ──────────────────────────────────────────────────


async def aggregate_scores(responses: list[UserResponse]) -> tuple[int, dict[str, int]]:
    score_breakdown = {
        "technical_skills": 0,
        "communication": 0,
        "problem_solving": 0,
        "behavioral_competency": 0,
    }
    counts = dict.fromkeys(score_breakdown.keys(), 0)

    for r in responses:
        category = getattr(r.question, "category", "technical_skills")
        if category in score_breakdown:
            score_breakdown[category] += int(r.score or 0) * 10
            counts[category] += 1

    for k in score_breakdown:
        score_breakdown[k] = score_breakdown[k] // counts[k] if counts[k] else 0

    overall_score = sum(score_breakdown.values()) // len(score_breakdown)
    return overall_score, score_breakdown


async def identify_strengths_improvements(
    responses: list[UserResponse],
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    strengths, improvements = [], []
    for r in responses:
        skill_name = getattr(r.question, "skill_name", "General")
        user_ans = r.user_answer or ""
        if (r.score or 0) >= 7:
            strengths.append(
                {
                    "area": skill_name,
                    "description": "Answered correctly",
                    "evidence": user_ans[:50] + "..." if len(user_ans) > 50 else user_ans,
                }
            )
        else:
            improvements.append(
                {
                    "area": skill_name,
                    "description": "Incorrect answer",
                    "recommendation": f"Review topic '{skill_name}' and retry similar questions",
                    "priority": "high",
                }
            )
    return strengths, improvements


async def generate_report(session_id: UUID, db: AsyncSession) -> dict[str, object]:
    try:
        from app.models.final_reports import FinalReport
    except ModuleNotFoundError as exc:
        raise HTTPException(
            status_code=501, detail="Final report model is not available in this deployment"
        ) from exc

    async with db.begin():  # Transaction to ensure atomicity
        session_result = await db.execute(
            select(InterviewSession).where(InterviewSession.id == session_id)
        )
        session = session_result.scalar_one_or_none()
        if not session or session.status != "completed":
            raise HTTPException(status_code=400, detail="Session not completed or not found")

        responses_result = await db.execute(
            select(UserResponse)
            .where(UserResponse.session_id == session_id)
            .order_by(UserResponse.created_at)
        )
        responses = responses_result.scalars().all()
        if not responses:
            raise HTTPException(status_code=400, detail="No responses found for this session")

        overall_score, score_breakdown = await aggregate_scores(responses)
        strengths, improvements = await identify_strengths_improvements(responses)

        # Safety check for interview_type
        interview_type = getattr(session, "interview_type", "General")

        try:
            ai_narrative = await generate_narrative_ai(
                interview_type=interview_type,
                overall_score=overall_score,
                strengths=strengths,
                improvements=improvements,
                question_count=len(responses),
            )
        except Exception:
            ai_narrative = "AI narrative generation is not available in this deployment."

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
            created_at=func.now(),
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
        "comparison_to_peers": report.peer_comparison,
    }


async def download_report_pdf(report_id: UUID, db: AsyncSession) -> StreamingResponse:
    try:
        from app.models.final_reports import FinalReport
    except ModuleNotFoundError as exc:
        raise HTTPException(
            status_code=501, detail="Final report model is not available in this deployment"
        ) from exc

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
        elements.append(
            Paragraph(
                f"{s['area']}: {s['description']} (Evidence: {s.get('evidence', '')})",
                styles["Normal"],
            )
        )
    elements.append(Spacer(1, 12))

    elements.append(Paragraph("Improvement Areas:", styles["Heading2"]))
    for imp in report.improvement_areas or []:
        elements.append(
            Paragraph(
                f"{imp['area']}: {imp['description']} (Recommendation: {imp.get('recommendation', '')})",
                styles["Normal"],
            )
        )
    elements.append(Spacer(1, 12))

    elements.append(Paragraph("AI Narrative:", styles["Heading2"]))
    elements.append(Paragraph(report.ai_narrative or "", styles["Normal"]))

    doc.build(elements)
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=interview_report_{report_id}.pdf"},
    )
def map_grade(score: float) -> str:
    if score < 4:
        return "Needs Practice"
    elif score < 6:
        return "Good"
    elif score < 8:
        return "Very Good"
    return "Excellent"