from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from fastapi import BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.behav_assessment_model import (
    AttemptStatus,
    BehavAttempt,
    BehavOption,
    BehavOptionScore,
    BehavQuestion,
    BehavUserAnswer,
)
from app.schemas.behav_assessment_schemas import SingleAnswer
from app.services.behav_ai_service import (
    generate_adaptive_questions,
    generate_assessment_questions,
    generate_personality_report,
)

TRAIT_MAP = {
    "honesty-humility": "Honesty-Humility",
    "emotionality": "Emotionality",
    "extraversion": "Extraversion",
    "agreeableness": "Agreeableness",
    "conscientiousness": "Conscientiousness",
    "openness": "Openness",
}


async def get_dynamic_questions(db: AsyncSession, user_id: UUID) -> dict[str, Any]:
    """
    Orchestrates the dynamic generation of 10 questions.
    1. Creates a new BehavAttempt.
    2. Generates new questions via AI (or mock).
    3. Saves new questions to DB.
    4. Returns the attempt_id and the newly generated questions.
    """
    # 1. Create a new attempt
    attempt = BehavAttempt(user_id=user_id, status=AttemptStatus.IN_PROGRESS)
    db.add(attempt)
    await db.flush()

    # 2. Generate 10 questions
    ai_questions = await generate_assessment_questions()

    # 3. Save to DB
    questions = await save_questions_bulk(db, ai_questions)

    return {"attempt_id": attempt.id, "questions": questions}


async def get_adaptive_questions_for_attempt(
    db: AsyncSession, attempt_id: UUID, traits: list[str]
) -> list[BehavQuestion]:
    """
    Dynamically generates adaptive questions for weak traits for a specific attempt.
    """
    # 1. Generate adaptive questions via AI
    ai_questions = await generate_adaptive_questions(traits)

    # 2. Save to DB (append to existing questions)
    return await save_questions_bulk(db, ai_questions)


async def submit_answer(
    db: AsyncSession, attempt_id: UUID, question_id: UUID, option_key: str
) -> None:
    stmt = select(BehavOption).where(
        BehavOption.question_id == question_id, BehavOption.option_key == option_key
    )
    result = await db.execute(stmt)
    option = result.scalar_one_or_none()

    if not option:
        raise ValueError("Invalid option")

    # Verify attempt exists and is in_progress
    attempt_stmt = select(BehavAttempt).where(BehavAttempt.id == attempt_id)
    attempt_result = await db.execute(attempt_stmt)
    attempt = attempt_result.scalar_one_or_none()
    if not attempt or attempt.status != AttemptStatus.IN_PROGRESS:
        raise ValueError("Invalid or inactive attempt")

    answer = BehavUserAnswer(
        attempt_id=attempt_id, question_id=question_id, option_id=option.id, user_id=attempt.user_id
    )
    db.add(answer)
    await db.commit()


async def submit_bulk_answers(
    db: AsyncSession, attempt_id: UUID, answers: list[SingleAnswer]
) -> None:
    # Verify attempt
    attempt_stmt = select(BehavAttempt).where(BehavAttempt.id == attempt_id)
    attempt_result = await db.execute(attempt_stmt)
    attempt = attempt_result.scalar_one_or_none()
    if not attempt or attempt.status != AttemptStatus.IN_PROGRESS:
        raise ValueError("Invalid or inactive attempt")

    for ans in answers:
        stmt = select(BehavOption).where(
            BehavOption.question_id == ans.question_id, BehavOption.option_key == ans.option_key
        )
        result = await db.execute(stmt)
        option = result.scalar_one_or_none()

        if option:
            answer = BehavUserAnswer(
                attempt_id=attempt_id,
                question_id=ans.question_id,
                option_id=option.id,
                user_id=attempt.user_id,
            )
            db.add(answer)

    await db.commit()


async def calculate_result(
    db: AsyncSession,
    attempt_id: UUID,
    trigger_hooks: bool = True,
    background_tasks: BackgroundTasks | None = None,
) -> dict[str, Any]:
    # Fetch attempt with answers
    stmt = (
        select(BehavAttempt)
        .options(joinedload(BehavAttempt.answers))
        .where(BehavAttempt.id == attempt_id)
    )
    result = await db.execute(stmt)
    attempt = result.unique().scalar_one_or_none()

    if not attempt:
        raise ValueError("Attempt not found")

    # If already submitted, return stored results
    if attempt.status == AttemptStatus.SUBMITTED and attempt.overall_report and attempt.scores:
        scores = attempt.scores or {}
        return {
            "attempt_id": attempt.id,
            "status": attempt.status,
            **scores,
            "ai_analysis": attempt.overall_report,
            "needs_adaptive_test": len(scores.get("weak_traits", [])) > 0,
        }

    answers = attempt.answers

    # HEXACO traits
    traits_list = [
        "honesty_humility",
        "emotionality",
        "extraversion",
        "agreeableness",
        "conscientiousness",
        "openness",
    ]

    total_scores = dict.fromkeys(traits_list, 0)
    counts = dict.fromkeys(traits_list, 0)

    for ans in answers:
        score_stmt = select(BehavOptionScore).where(BehavOptionScore.option_id == ans.option_id)
        score_result = await db.execute(score_stmt)
        score_objs = score_result.scalars().all()

        for score_obj in score_objs:
            trait = score_obj.trait_name
            if trait in traits_list:
                val = score_obj.score_value
                if val > 0:
                    total_scores[trait] += val
                    counts[trait] += 1

    analysis_percentage = {}
    weak_traits = []
    strong_traits = []

    for trait in traits_list:
        count = counts[trait]
        display_name = TRAIT_MAP.get(trait, trait.replace("_", "-").title())

        if count > 0:
            max_possible = count * 5
            percentage = (total_scores[trait] / max_possible) * 100
            analysis_percentage[trait] = round(percentage, 2)

            if percentage < 60:
                weak_traits.append(display_name)
            elif percentage >= 80:
                strong_traits.append(display_name)
        else:
            analysis_percentage[trait] = 0.0
            weak_traits.append(display_name)

    meaningful_scores = {t: s for t, s in analysis_percentage.items() if counts[t] > 0}
    comparative_low_traits = []
    if meaningful_scores:
        min_score = min(meaningful_scores.values())
        for trait, score in meaningful_scores.items():
            if score == min_score:
                display_name = TRAIT_MAP.get(trait, trait.replace("_", "-").title())
                comparative_low_traits.append(display_name)
    else:
        comparative_low_traits = weak_traits.copy()

    try:
        avg_scores_for_ai = {t: round(v / 20.0, 2) for t, v in analysis_percentage.items()}
        ai_report_json = await generate_personality_report(avg_scores_for_ai)
    except Exception as e:
        ai_report_json = {"summary": "AI Error", "error": str(e)}

    recommendation = ""
    if comparative_low_traits:
        traits_str = ", ".join(comparative_low_traits)
        recommendation = (
            f"Your score in {traits_str} is comparatively lower. "
            "This can be balanced by practicing a little more in these areas."
        )

    full_results = {
        "hexaco_scores": analysis_percentage,
        "weak_traits": weak_traits,
        "strong_traits": strong_traits,
        "comparative_low_traits": comparative_low_traits,
        "recommendation": recommendation,
        "needs_adaptive_test": len(weak_traits) > 0,
    }

    # Persist in BehavAttempt
    attempt.status = AttemptStatus.SUBMITTED
    attempt.submitted_at = datetime.now(UTC).replace(tzinfo=None)
    attempt.scores = full_results
    attempt.overall_report = ai_report_json
    await db.commit()

    # ── Post-Evaluation Hook ────────────────────────────────────────────────
    # Calls Learning Path service to recommend modules based on personality results.
    # Wire this as a non-blocking background task.
    if trigger_hooks:
        if background_tasks:
            background_tasks.add_task(_trigger_learning_path_hook, attempt.user_id, attempt.id)
        else:
            import logging

            logging.getLogger(__name__).warning(
                "BackgroundTasks not provided; triggered learning path hook skipped."
            )

    return {
        "attempt_id": attempt.id,
        "status": attempt.status,
        **full_results,
        "ai_analysis": ai_report_json,
        "needs_adaptive_test": len(weak_traits) > 0,
    }


# --- Database Helpers ---


async def save_questions_bulk(db: AsyncSession, questions_data: list[Any]) -> list[BehavQuestion]:
    keys = ["A", "B", "C", "D"]
    created_questions = []

    for q_data in questions_data:
        question = BehavQuestion(question_text=q_data.question_text, trait_type=q_data.trait)
        db.add(question)
        await db.flush()
        created_questions.append(question)

        for idx, opt_ai in enumerate(q_data.options):
            if idx >= 4:
                break

            option = BehavOption(
                question_id=question.id, option_key=keys[idx], option_text=opt_ai.option_text
            )
            db.add(option)
            await db.flush()

            trait_key = q_data.trait.lower().replace("-", "_")
            score = BehavOptionScore(
                option_id=option.id, trait_name=trait_key, score_value=opt_ai.score
            )
            db.add(score)

    await db.commit()

    # Reload questions with options to return full objects
    stmt = (
        select(BehavQuestion)
        .where(BehavQuestion.id.in_([q.id for q in created_questions]))
        .options(joinedload(BehavQuestion.options))
    )
    result = await db.execute(stmt)
    return list(result.unique().scalars().all())


async def _trigger_learning_path_hook(user_id: UUID, attempt_id: UUID) -> None:
    """
    Background hook to process learning path updates without blocking
    the main assessment response.
    """
    from app.config.database import AsyncSessionLocal
    from app.services.behav_learning_hook import behav_learning_service

    try:
        async with AsyncSessionLocal() as db:
            await behav_learning_service.process_assessment_completion(
                db, user_id, attempt_id, internal_call=True
            )
    except Exception as e:
        # Since this is a background task, we must handle exceptions
        # to prevent it from crashing the event loop silently or noisily.
        import logging

        logging.getLogger(__name__).error(f"Error in Learning Path hook: {e!s}")
