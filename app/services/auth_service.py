import hashlib
from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
import httpx
from fastapi import HTTPException, status
from jose import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import get_settings
from app.models.user import User
from app.schemas.auth import AuthResponse, LoginRequest, SignupRequest, UserResponse

settings = get_settings()


async def verify_google_id_token(id_token: str) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            settings.google_tokeninfo_url,
            params={"id_token": id_token},
        )

    if response.status_code != status.HTTP_200_OK:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google OAuth token",
        )

    token_payload = response.json()

    if settings.google_client_id and token_payload.get("aud") != settings.google_client_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google token audience mismatch",
        )

    if not token_payload.get("email"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google token did not contain an email",
        )

    return token_payload


async def exchange_google_oauth_code(
    oauth_code: str,
    oauth_redirect_uri: str | None,
    oauth_code_verifier: str | None,
) -> dict[str, Any]:
    token_request_payload: dict[str, str] = {
        "code": oauth_code,
        "client_id": settings.google_client_id or "",
        "grant_type": "authorization_code",
    }

    if not settings.google_client_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GOOGLE_CLIENT_ID is required for OAuth code flow",
        )

    if oauth_redirect_uri:
        token_request_payload["redirect_uri"] = oauth_redirect_uri

    if oauth_code_verifier:
        token_request_payload["code_verifier"] = oauth_code_verifier

    if settings.google_client_secret:
        token_request_payload["client_secret"] = settings.google_client_secret

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(settings.google_token_url, data=token_request_payload)

    if response.status_code != status.HTTP_200_OK:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google OAuth code",
        )

    token_data = response.json()
    id_token = token_data.get("id_token")
    if not id_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google token exchange did not return id_token",
        )

    return await verify_google_id_token(str(id_token))


def hash_password(password: str) -> str:
    sha256_hash = hashlib.sha256(password.encode()).hexdigest()
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(sha256_hash.encode(), salt)
    return hashed.decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    sha256_hash = hashlib.sha256(plain_password.encode()).hexdigest()
    return bcrypt.checkpw(sha256_hash.encode(), hashed_password.encode())


def get_expiration_delta(remember_me: bool) -> timedelta:
    if remember_me:
        return timedelta(days=settings.refresh_token_expire_days)
    return timedelta(minutes=settings.access_token_expire_minutes)


def create_access_token(
    subject: str,
    email: str,
    remember_me: bool,
    role: str = "user",
) -> tuple[str, int]:
    expiration_delta = get_expiration_delta(remember_me)
    expires_in = int(expiration_delta.total_seconds())
    expires_at = datetime.now(UTC) + expiration_delta

    payload = {
        "sub": subject,
        "email": email,
        "role": role,
        "exp": expires_at,
    }

    token = jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)

    return token, expires_in


async def signup_user(db: AsyncSession, signup_payload: SignupRequest) -> AuthResponse:
    normalized_email = signup_payload.email.lower()

    existing_user_stmt = select(User).where(User.email == normalized_email)
    existing_user = await db.scalar(existing_user_stmt)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
        )

    oauth_provider: str | None = None
    oauth_sub: str | None = None
    password_hash: str | None = None
    remember_me = signup_payload.remember_me

    if signup_payload.oauth_id_token or signup_payload.oauth_code:
        if signup_payload.oauth_id_token:
            google_data = await verify_google_id_token(signup_payload.oauth_id_token)
        else:
            google_data = await exchange_google_oauth_code(
                oauth_code=str(signup_payload.oauth_code),
                oauth_redirect_uri=signup_payload.oauth_redirect_uri,
                oauth_code_verifier=signup_payload.oauth_code_verifier,
            )
        google_email = str(google_data["email"]).lower()

        if google_email != normalized_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email does not match Google account",
            )

        oauth_provider = "google"
        oauth_sub = str(google_data.get("sub")) if google_data.get("sub") else None
        remember_me = True
    else:
        if signup_payload.password is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password is required",
            )
        password_hash = hash_password(signup_payload.password)

    new_user = User(
        email=normalized_email,
        password_hash=password_hash,
        oauth_provider=oauth_provider,
        oauth_sub=oauth_sub,
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    access_token, expires_in = create_access_token(str(new_user.id), new_user.email, remember_me)

    return AuthResponse(
        access_token=access_token,
        expires_in=expires_in,
        remember_me=remember_me,
        profile_completed=new_user.profile_completed,
        user=UserResponse.model_validate(new_user),
    )


async def login_user(db: AsyncSession, login_payload: LoginRequest) -> AuthResponse:
    remember_me = login_payload.remember_me

    if login_payload.oauth_id_token or login_payload.oauth_code:
        if login_payload.oauth_id_token:
            google_data = await verify_google_id_token(login_payload.oauth_id_token)
        else:
            google_data = await exchange_google_oauth_code(
                oauth_code=str(login_payload.oauth_code),
                oauth_redirect_uri=login_payload.oauth_redirect_uri,
                oauth_code_verifier=login_payload.oauth_code_verifier,
            )
        normalized_email = str(google_data["email"]).lower()
        remember_me = True

        user_stmt = select(User).where(User.email == normalized_email)
        user = await db.scalar(user_stmt)

        if not user:
            user = User(
                email=normalized_email,
                password_hash=None,
                oauth_provider="google",
                oauth_sub=str(google_data.get("sub")) if google_data.get("sub") else None,
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)

        access_token, expires_in = create_access_token(str(user.id), user.email, remember_me)
        return AuthResponse(
            access_token=access_token,
            expires_in=expires_in,
            remember_me=remember_me,
            profile_completed=user.profile_completed,
            user=UserResponse.model_validate(user),
        )

    if login_payload.email is None or login_payload.password is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email and password are required",
        )

    normalized_email = login_payload.email.lower()
    user_stmt = select(User).where(User.email == normalized_email)
    user = await db.scalar(user_stmt)

    if not user or not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not verify_password(login_payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    access_token, expires_in = create_access_token(str(user.id), user.email, remember_me)

    return AuthResponse(
        access_token=access_token,
        expires_in=expires_in,
        remember_me=remember_me,
        profile_completed=user.profile_completed,
        user=UserResponse.model_validate(user),
    )
