from dataclasses import dataclass
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.learning_path import LearningPath, ModuleUnlock
from app.schemas.learning_path import AssessmentResults


CEFR_BANDS: list[tuple[int, str]] = [
    (20, "A1"),
    (40, "A2"),
    (55, "B1"),
    (70, "B2"),
    (85, "C1"),
    (101, "C2"),
]

GOAL_MODULES: dict[str, list[str]] = {
    "placement_prep": ["mock_interview", "gd_skills", "resume_building"],
    "promotion": ["presentation_skills", "leadership_communication", "stakeholder_updates"],
    "entrepreneurship": ["pitching", "client_communication", "negotiation"],
}

CORE_MODULE_SCORES = {
    "grammar": "grammar_score",
    "reading": "reading_score",
    "listening": "listening_score",
    "speaking": "speaking_score",
}


@dataclass
class ComputedPath:
    cefr_level: str
    recommended_path: list[dict]
    weak_areas: list[str]
    estimated_completion_weeks: int


def map_score_to_cefr(avg_score: float) -> str:
    for upper_bound, level in CEFR_BANDS:
        if avg_score < upper_bound:
            return level
    return "C2"


def map_score_to_start_level(score: int) -> str:
    if score < 60:
        return "basic"
    if score < 80:
        return "intermediate"
    return "advanced"


def map_cefr_to_start_level(cefr_level: str) -> str:
    if cefr_level in {"A1", "A2"}:
        return "basic"
    if cefr_level in {"B1", "B2"}:
        return "intermediate"
    return "advanced"


def _estimate_completion_weeks(weak_areas_count: int, user_goal: str) -> int:
    base = 4 + weak_areas_count
    if user_goal == "placement_prep":
        return base + 1
    return base


def compute_learning_path(assessment: AssessmentResults, user_goal: str) -> ComputedPath:
    scores = {
        "grammar": assessment.grammar_score,
        "reading": assessment.reading_score,
        "listening": assessment.listening_score,
        "speaking": assessment.speaking_score,
        "pronunciation": assessment.speaking_score,
    }

    avg_score = (
        assessment.grammar_score
        + assessment.reading_score
        + assessment.listening_score
        + assessment.speaking_score
    ) / 4
    cefr_level = map_score_to_cefr(avg_score)

    weak_areas = [module for module, score in scores.items() if module != "pronunciation" and score < 65]
    weak_areas = sorted(weak_areas, key=lambda module: scores[module])

    ordered_modules: list[str] = []
    ordered_modules.extend(weak_areas)

    if "speaking" in weak_areas and "pronunciation" not in ordered_modules:
        ordered_modules.append("pronunciation")

    for goal_module in GOAL_MODULES[user_goal]:
        if goal_module not in ordered_modules:
            ordered_modules.append(goal_module)

    # Ensure at least one foundational module is always present.
    if not ordered_modules:
        ordered_modules.append("grammar")

    recommended_path: list[dict] = []
    for idx, module in enumerate(ordered_modules[:6], start=1):
        if module in scores:
            start_level = map_score_to_start_level(scores[module])
        else:
            start_level = map_cefr_to_start_level(cefr_level)

        recommended_path.append(
            {
                "module": module,
                "start_level": start_level,
                "priority": idx,
            }
        )

    return ComputedPath(
        cefr_level=cefr_level,
        recommended_path=recommended_path,
        weak_areas=weak_areas,
        estimated_completion_weeks=_estimate_completion_weeks(len(weak_areas), user_goal),
    )


class LearningPathService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def assign_learning_path(
        self, user_id: UUID, assessment: AssessmentResults, user_goal: str
    ) -> dict:
        computed = compute_learning_path(assessment, user_goal)

        existing = await self.db.execute(select(LearningPath).where(LearningPath.user_id == user_id))
        path = existing.scalar_one_or_none()

        if path is None:
            path = LearningPath(
                user_id=user_id,
                cefr_level=computed.cefr_level,
                assigned_modules=computed.recommended_path,
                user_goal=user_goal,
            )
            self.db.add(path)
        else:
            path.cefr_level = computed.cefr_level
            path.assigned_modules = computed.recommended_path
            path.user_goal = user_goal

        await self.db.execute(delete(ModuleUnlock).where(ModuleUnlock.user_id == user_id))
        for module in computed.recommended_path:
            self.db.add(
                ModuleUnlock(
                    id=uuid4(),
                    user_id=user_id,
                    module_name=module["module"],
                    unlocked_level=module["start_level"],
                )
            )

        await self.db.commit()

        return {
            "user_id": user_id,
            "cefr_level": computed.cefr_level,
            "recommended_path": computed.recommended_path,
            "weak_areas": computed.weak_areas,
            "estimated_completion_weeks": computed.estimated_completion_weeks,
        }

    async def get_learning_path(self, user_id: UUID) -> dict:
        result = await self.db.execute(select(LearningPath).where(LearningPath.user_id == user_id))
        path = result.scalar_one_or_none()
        if path is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Learning path not found")

        unlocks_result = await self.db.execute(select(ModuleUnlock).where(ModuleUnlock.user_id == user_id))
        unlocks = unlocks_result.scalars().all()

        recommended_path = path.assigned_modules or []
        total_modules = len(recommended_path)
        unlocked_modules = len(unlocks)
        completion_pct = round((unlocked_modules / total_modules) * 100, 2) if total_modules else 0.0

        weak_areas = [
            item["module"]
            for item in recommended_path
            if item.get("module") in {"grammar", "reading", "listening", "speaking"}
            and item.get("start_level") == "basic"
        ]

        return {
            "user_id": user_id,
            "cefr_level": path.cefr_level,
            "recommended_path": recommended_path,
            "weak_areas": weak_areas,
            "estimated_completion_weeks": max(4, total_modules),
            "progress": {
                "total_modules": total_modules,
                "unlocked_modules": unlocked_modules,
                "completion_pct": completion_pct,
            },
        }

    async def recalculate_learning_path(
        self,
        user_id: UUID,
        assessment: AssessmentResults,
        user_goal: str | None = None,
    ) -> dict:
        existing = await self.db.execute(select(LearningPath).where(LearningPath.user_id == user_id))
        path = existing.scalar_one_or_none()
        if path is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Learning path not found")

        goal = user_goal or path.user_goal
        return await self.assign_learning_path(user_id=user_id, assessment=assessment, user_goal=goal)
