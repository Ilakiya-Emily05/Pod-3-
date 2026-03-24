from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import AdminUser
from app.schemas.admin import AdminAuthResponse, AdminSignupRequest
from app.services.auth_service import create_access_token, hash_password


async def admin_signup(db: AsyncSession, signup_payload: AdminSignupRequest) -> AdminAuthResponse:
    if not signup_payload.passwords_match:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password and confirm_password must match",
        )

    normalized_email = str(signup_payload.email).strip().lower()
    existing_admin_stmt = select(AdminUser).where(AdminUser.email == normalized_email)
    existing_admin = await db.scalar(existing_admin_stmt)

    if existing_admin:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An admin with this email already exists",
        )

    new_admin = AdminUser(
        email=normalized_email,
        password_hash=hash_password(signup_payload.password),
    )
    db.add(new_admin)
    await db.commit()
    await db.refresh(new_admin)

    access_token, expires_in = create_access_token(
        subject=str(new_admin.id),
        email=new_admin.email,
        remember_me=False,
        role="admin",
    )

    return AdminAuthResponse(
        access_token=access_token,
        expires_in=expires_in,
        admin_email=new_admin.email,
    )
