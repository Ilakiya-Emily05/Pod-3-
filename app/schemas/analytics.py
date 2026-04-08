from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class GrammarModuleProgress(BaseModel):
    completion_pct: float = Field(default=0.0, ge=0.0, le=100.0)
    avg_score: float = Field(default=0.0, ge=0.0, le=100.0)
    weak_topics: list[str] = Field(default_factory=list)


class PronunciationModuleProgress(BaseModel):
    completion_pct: float = Field(default=0.0, ge=0.0, le=100.0)
    current_level: str | None = None


class BehavioralModuleProgress(BaseModel):
    completed: bool = False
    hexaco_summary: dict[str, Any] | None = None


class AnalyticsModuleBreakdown(BaseModel):
    grammar: GrammarModuleProgress
    pronunciation: PronunciationModuleProgress
    behavioral: BehavioralModuleProgress


class AnalyticsProgressResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: UUID
    overall_completion_pct: float = Field(ge=0.0, le=100.0)
    cefr_level: str | None = None
    modules: AnalyticsModuleBreakdown
    streak_days: int = Field(ge=0)
    last_activity: datetime | None = None


class HeatmapTopicItem(BaseModel):
    name: str
    score: float = Field(ge=0.0, le=100.0)
    status: str


class AnalyticsHeatmapResponse(BaseModel):
    topics: list[HeatmapTopicItem] = Field(default_factory=list)


class TrendPoint(BaseModel):
    date: datetime
    avg_score: float | None = Field(default=None, ge=0.0, le=100.0)


class AnalyticsTrendsResponse(BaseModel):
    period: str
    data: list[TrendPoint] = Field(default_factory=list)
