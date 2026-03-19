from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserProfile
from app.schemas.onboarding import OnboardingRequest, OnboardingResponse


async def complete_onboarding(
    user_id: UUID, db: AsyncSession, onboarding_payload: OnboardingRequest
) -> OnboardingResponse:
    user_stmt = select(User).where(User.id == user_id)
    user = await db.scalar(user_stmt)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    existing_profile_stmt = select(UserProfile).where(UserProfile.user_id == user_id)
    existing_profile = await db.scalar(existing_profile_stmt)

    if existing_profile:
        existing_profile.name = onboarding_payload.name
        existing_profile.mobile = onboarding_payload.mobile
        existing_profile.dob = onboarding_payload.dob
        existing_profile.college = onboarding_payload.college
    else:
        existing_profile = UserProfile(
            user_id=user_id,
            name=onboarding_payload.name,
            mobile=onboarding_payload.mobile,
            dob=onboarding_payload.dob,
            college=onboarding_payload.college,
        )
        db.add(existing_profile)

    user.profile_completed = True
    await db.commit()
    await db.refresh(existing_profile)

    return OnboardingResponse(
        profile=existing_profile,
    )
