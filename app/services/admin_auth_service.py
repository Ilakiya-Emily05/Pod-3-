import hmac

from fastapi import HTTPException, status

from app.config.settings import get_settings
from app.schemas.admin import AdminAuthResponse, AdminLoginRequest
from app.services.auth_service import create_access_token, verify_password

settings = get_settings()


def admin_login(login_payload: AdminLoginRequest) -> AdminAuthResponse:
    configured_email = (settings.admin_email or "").strip().lower()
    configured_password_hash = settings.admin_password_hash

    if not configured_email or not configured_password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin credentials",
        )

    submitted_email = str(login_payload.email).strip().lower()
    email_matches = hmac.compare_digest(submitted_email, configured_email)
    password_matches = verify_password(login_payload.password, configured_password_hash)

    if not email_matches or not password_matches:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin credentials",
        )

    access_token, expires_in = create_access_token(
        subject=submitted_email,
        email=submitted_email,
        remember_me=False,
        role="admin",
    )

    return AdminAuthResponse(
        access_token=access_token,
        expires_in=expires_in,
        admin_email=submitted_email,
    )
