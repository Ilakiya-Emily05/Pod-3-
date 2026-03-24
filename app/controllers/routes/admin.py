from fastapi import APIRouter, status

from app.schemas.admin import AdminAuthResponse, AdminLoginRequest
from app.services.admin_auth_service import admin_login

router = APIRouter(prefix="/admin/auth", tags=["Admin Auth"])


@router.post("/login", response_model=AdminAuthResponse, status_code=status.HTTP_200_OK)
async def login_admin(payload: AdminLoginRequest) -> AdminAuthResponse:
    return admin_login(payload)
