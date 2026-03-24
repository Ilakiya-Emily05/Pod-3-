from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.controllers.admin import AdminController
from app.schemas.admin import (
    AdminAuthResponse,
    AdminLoginRequest,
    AnalyticsSummary,
    QuestionCreate,
    UsersListResponse,
)
from app.services.admin_auth_service import admin_login

router = APIRouter(prefix="/admin", tags=["Admin APIs"])


@router.post(
    "/auth/login",
    response_model=AdminAuthResponse,
    status_code=status.HTTP_200_OK,
    summary="Admin login",
    description="Authenticate admin and return bearer token",
)
async def login_admin(payload: AdminLoginRequest) -> AdminAuthResponse:
    return admin_login(payload)


@router.get(
    "/users",
    response_model=UsersListResponse,
    status_code=status.HTTP_200_OK,
    summary="List all users (Admin)",
    description="Get paginated list of users with optional search",
)
async def list_users(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    search: str | None = Query(None, description="Search by email"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a paginated list of all users.
    
    - **page**: Page number (default: 1)
    - **page_size**: Items per page (1-100, default: 20)
    - **search**: Optional search term for email
    """
    controller = AdminController(db)
    return await controller.get_users(page=page, page_size=page_size, search=search)


@router.get(
    "/analytics",
    response_model=AnalyticsSummary,
    status_code=status.HTTP_200_OK,
    summary="Get platform analytics (Admin)",
    description="Get comprehensive platform analytics and statistics",
)
async def get_analytics(
    db: AsyncSession = Depends(get_db),
):
    """
    Get platform-wide analytics including:
    
    - Total and active users
    - Assessment statistics
    - Average scores
    - Completion rates
    - Recent activity
    """
    controller = AdminController(db)
    return await controller.get_analytics()


@router.post(
    "/questions",
    status_code=status.HTTP_201_CREATED,
    summary="Create question (Admin)",
    description="Create a new question for any assessment type",
)
async def create_question(
    data: QuestionCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a question for an assessment (admin only).
    
    - **assessment_type**: Type of assessment (reading, listening, grammar)
    - **assessment_id**: ID of the assessment
    - **question_text**: The question content
    - **sort_order**: Display order
    - **points**: Points for this question
    - **options**: List of options with is_correct flag
    """
    controller = AdminController(db)
    try:
        result = await controller.create_question(data)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
