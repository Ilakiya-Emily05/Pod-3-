from uuid import UUID

from pydantic import BaseModel, Field


class AssessmentResults(BaseModel):
    grammar_score: int = Field(ge=0, le=100)
    reading_score: int = Field(ge=0, le=100)
    listening_score: int = Field(ge=0, le=100)
    speaking_score: int = Field(ge=0, le=100)


class LearningPathCreate(BaseModel):
    user_id: UUID
    assessment_results: AssessmentResults
    user_goal: str = Field(pattern="^(placement_prep|promotion|entrepreneurship)$")


class RecalculateLearningPathRequest(BaseModel):
    assessment_results: AssessmentResults
    user_goal: str | None = Field(
        default=None, pattern="^(placement_prep|promotion|entrepreneurship)$"
    )


class ModuleRecommendation(BaseModel):
    module: str
    start_level: str
    priority: int


class LearningPathProgress(BaseModel):
    total_modules: int
    unlocked_modules: int
    completion_pct: float


class LearningPathRead(BaseModel):
    user_id: UUID
    cefr_level: str
    recommended_path: list[ModuleRecommendation]
    weak_areas: list[str]
    estimated_completion_weeks: int
    progress: LearningPathProgress | None = None


# Backward-compatible aliases for existing imports.
AssignLearningPathRequest = LearningPathCreate
LearningPathResponse = LearningPathRead
