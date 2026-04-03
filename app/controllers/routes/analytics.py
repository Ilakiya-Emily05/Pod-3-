from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.schemas.analytics import (
    AnalyticsHeatmapResponse,
    AnalyticsProgressResponse,
    AnalyticsTrendsResponse,
)
from app.services.analytics_service import AnalyticsService
from app.utils.auth import get_current_user_id

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get(
    "/progress/{user_id}",
    response_model=AnalyticsProgressResponse,
    status_code=status.HTTP_200_OK,
    summary="Get aggregated user progress analytics",
)
async def get_user_analytics_progress(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
) -> AnalyticsProgressResponse:
    if user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to access this user's analytics",
        )

    service = AnalyticsService(db)
    return await service.get_progress(user_id)


@router.get(
    "/heatmap/{user_id}",
    response_model=AnalyticsHeatmapResponse,
    status_code=status.HTTP_200_OK,
    summary="Get topic-level analytics heatmap",
)
async def get_user_analytics_heatmap(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
) -> AnalyticsHeatmapResponse:
    if user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to access this user's analytics",
        )

    service = AnalyticsService(db)
    return await service.get_heatmap(user_id)


@router.get(
    "/trends/{user_id}",
    response_model=AnalyticsTrendsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get score trends over time",
)
async def get_user_analytics_trends(
    user_id: UUID,
    period: str = Query(default="30d"),
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
) -> AnalyticsTrendsResponse:
    if user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to access this user's analytics",
        )

    service = AnalyticsService(db)
    try:
        return await service.get_trends(user_id, period)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
