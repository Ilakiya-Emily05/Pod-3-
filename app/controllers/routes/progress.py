from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.controllers.progress import ProgressController
from app.schemas.progress import (
    ProgressComplete,
    ProgressResponse,
    ProgressStart,
    UserProgressSummary,
)

router = APIRouter(prefix="/progress", tags=["Progress Tracking"])


@router.post(
    "/start-module",
    response_model=ProgressResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start a learning module",
    description="Start or resume tracking progress for a learning module",
)
async def start_module(
    data: ProgressStart,
    db: AsyncSession = Depends(get_db),
):
    """
    Start tracking progress for a module.
    
    - **user_id**: ID of the user starting the module
    - **module_type**: Type of module (reading, listening, grammar)
    - **module_id**: ID of the assessment/module
    """
    controller = ProgressController(db)
    return await controller.start_module(data)


@router.post(
    "/complete-module/{user_id}/{module_type}/{module_id}",
    response_model=ProgressResponse,
    status_code=status.HTTP_200_OK,
    summary="Complete a learning module",
    description="Mark a module as completed with final score",
)
async def complete_module(
    user_id: UUID,
    module_type: str,
    module_id: UUID,
    data: ProgressComplete,
    db: AsyncSession = Depends(get_db),
):
    """
    Complete a module and record the score.
    
    - **user_id**: ID of the user completing the module
    - **module_type**: Type of module (reading, listening, grammar)
    - **module_id**: ID of the assessment/module
    - **score**: Final score achieved
    - **total_questions**: Total questions in the module
    - **correct_answers**: Number of correct answers
    """
    if module_type not in ["reading", "listening", "grammar"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid module type. Must be reading, listening, or grammar",
        )

    controller = ProgressController(db)
    return await controller.complete_module(user_id, module_type, module_id, data)


@router.get(
    "/users/{user_id}",
    response_model=list[ProgressResponse],
    status_code=status.HTTP_200_OK,
    summary="Get user progress history",
    description="Retrieve all progress records for a specific user",
)
async def get_user_progress(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get all progress records for a user.
    
    Returns a list of all modules the user has started or completed.
    """
    controller = ProgressController(db)
    return await controller.get_user_progress(user_id)


@router.get(
    "/users/{user_id}/summary",
    response_model=UserProgressSummary,
    status_code=status.HTTP_200_OK,
    summary="Get user progress summary",
    description="Get summarized statistics of user's progress",
)
async def get_user_progress_summary(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get a summary of user's progress across all modules.
    
    Returns:
    - Total modules started
    - Total modules completed
    - Average score
    - Breakdown by module type
    """
    controller = ProgressController(db)
    return await controller.get_user_progress_summary(user_id)
