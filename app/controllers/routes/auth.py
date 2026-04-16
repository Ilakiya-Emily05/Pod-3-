from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.schemas.auth import (
    AuthLoginResponse,
    AuthRegisterResponse,
    UserCreate,
    UserLogin,
    UserRead,
)
from app.services.auth_service import get_current_user_profile, login_user, register_user
from app.utils.auth import CurrentUser, get_current_user

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/register",
    response_model=AuthRegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(payload: UserCreate, db: AsyncSession = Depends(get_db)) -> AuthRegisterResponse:
    return await register_user(db, payload)


@router.post("/login", response_model=AuthLoginResponse, status_code=status.HTTP_200_OK)
async def login(payload: UserLogin, db: AsyncSession = Depends(get_db)) -> AuthLoginResponse:
    return await login_user(db, payload)


@router.get("/me", response_model=UserRead, status_code=status.HTTP_200_OK)
async def me(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserRead:
    return await get_current_user_profile(db, current_user)
