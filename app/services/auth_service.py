import hashlib
import logging
from datetime import UTC, datetime, timedelta

import bcrypt
from fastapi import HTTPException, status
from jose import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import get_settings
from app.models.user import User
from app.schemas.auth import (
    AuthLoginResponse,
    AuthRegisterResponse,
    UserCreate,
    UserLogin,
    UserRead,
)
from app.services.analytics_service import AnalyticsService
from app.utils.auth import CurrentUser

settings = get_settings()
logger = logging.getLogger(__name__)


def hash_password(password: str) -> str:
    sha256_hash = hashlib.sha256(password.encode()).hexdigest()
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(sha256_hash.encode(), salt)
    return hashed.decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    sha256_hash = hashlib.sha256(plain_password.encode()).hexdigest()
    try:
        return bcrypt.checkpw(sha256_hash.encode(), hashed_password.encode())
    except ValueError:
        return False


def _build_token_payload(
    subject: str,
    email: str,
    name: str,
    role: str,
    token_type: str,
    expiration_delta: timedelta,
) -> dict[str, object]:
    issued_at = datetime.now(UTC)
    expires_at = issued_at + expiration_delta

    return {
        "sub": subject,
        "email": email,
        "name": name,
        "role": role,
        "token_type": token_type,
        "iat": int(issued_at.timestamp()),
        "exp": int(expires_at.timestamp()),
    }


def _encode_token(
    subject: str,
    email: str,
    name: str,
    role: str,
    token_type: str,
    expiration_delta: timedelta,
) -> str:
    payload = _build_token_payload(subject, email, name, role, token_type, expiration_delta)
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def create_access_token(
    subject: str,
    email: str,
    remember_me: bool,
    name: str | None = None,
    role: str = "student",
) -> tuple[str, int]:
    expiration_delta = (
        timedelta(days=settings.refresh_token_expire_days)
        if remember_me
        else timedelta(minutes=settings.access_token_expire_minutes)
    )
    expires_in = int(expiration_delta.total_seconds())
    access_label = "access"
    token = _encode_token(
        subject=subject,
        email=email,
        name=name or "",
        role=role,
        token_type=access_label,
        expiration_delta=expiration_delta,
    )
    return token, expires_in


def create_refresh_token(
    subject: str,
    email: str,
    name: str | None = None,
    role: str = "student",
) -> tuple[str, int]:
    expiration_delta = timedelta(days=settings.refresh_token_expire_days)
    expires_in = int(expiration_delta.total_seconds())
    refresh_label = "refresh"
    token = _encode_token(
        subject=subject,
        email=email,
        name=name or "",
        role=role,
        token_type=refresh_label,
        expiration_delta=expiration_delta,
    )
    return token, expires_in


async def register_user(db: AsyncSession, payload: UserCreate) -> AuthRegisterResponse:
    normalized_email = payload.email.strip().lower()
    existing_user = await db.scalar(select(User).where(User.email == normalized_email))
    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
        )

    user = User(
        name=payload.name.strip(),
        email=normalized_email,
        password_hash=hash_password(payload.password),
        streak_count=0,
        total_xp=0,
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    token, _ = create_access_token(str(user.id), user.email, remember_me=False, name=user.name)
    return AuthRegisterResponse(user_id=user.id, token=token)


async def login_user(db: AsyncSession, payload: UserLogin) -> AuthLoginResponse:
    normalized_email = payload.email.strip().lower()
    user = await db.scalar(select(User).where(User.email == normalized_email))

    if user is None or user.password_hash is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    user.last_active_date = datetime.now(UTC).date()
    await db.commit()
    await db.refresh(user)

    access_token, _ = create_access_token(
        str(user.id),
        user.email,
        remember_me=False,
        name=user.name,
    )
    refresh_token, _ = create_refresh_token(str(user.id), user.email, name=user.name)
    return AuthLoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=await _build_user_read(db, user),
    )


async def get_current_user_profile(db: AsyncSession, current_user: CurrentUser) -> UserRead:
    user = await db.scalar(select(User).where(User.id == current_user.user_id))
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return await _build_user_read(db, user)


async def _build_user_read(db: AsyncSession, user: User) -> UserRead:
    cefr_level: str | None = None
    try:
        progress = await AnalyticsService(db).get_progress(user.id)
        cefr_level = progress.cefr_level
    except Exception:
        logger.exception(
            "Failed to fetch CEFR level for user profile",
            extra={"user_id": str(user.id)},
        )

    return UserRead(
        id=user.id,
        email=user.email,
        name=user.name,
        cefr_level=cefr_level,
        learning_goal=user.learning_goal,
        learning_frequency=user.learning_frequency,
        streak_count=int(user.streak_count or 0),
        total_xp=int(user.total_xp or 0),
    )
