from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.schemas.admin import (
    AdminAuthResponse,
    AdminSignupRequest,
)
from app.services.admin_auth_service import admin_signup

router = APIRouter(prefix="/admin", tags=["Admin APIs"])

@router.post(
    "/auth/signup",
    response_model=AdminAuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Admin signup",
    description="Create an admin account and return bearer token",
)
async def signup_admin(
    payload: AdminSignupRequest,
    db: AsyncSession = Depends(get_db),
) -> AdminAuthResponse:
    return await admin_signup(db, payload)
