from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.schemas.onboarding import OnboardingRequest, OnboardingResponse
from app.services.onboarding_service import complete_onboarding
from app.utils.auth import get_current_user_id

router = APIRouter(prefix="/onboarding", tags=["Onboarding"])


@router.post("", response_model=OnboardingResponse, status_code=status.HTTP_201_CREATED)
async def onboarding(
    payload: OnboardingRequest,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> OnboardingResponse:
    return await complete_onboarding(user_id, db, payload)
