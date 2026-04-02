from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.schemas.analytics import AnalyticsProgressResponse
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
