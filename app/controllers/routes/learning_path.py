from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.schemas.learning_path import (
    AssignLearningPathRequest,
    LearningPathResponse,
    RecalculateLearningPathRequest,
)
from app.services.learning_path_service import LearningPathService
from app.utils.auth import get_current_user_id

router = APIRouter(prefix="/learning-path", tags=["learning-path"])


@router.post("/assign", response_model=LearningPathResponse, status_code=status.HTTP_201_CREATED)
async def assign_learning_path(
    payload: AssignLearningPathRequest,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
) -> LearningPathResponse:
    if payload.user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to assign another user's learning path",
        )

    service = LearningPathService(db)
    result = await service.assign_learning_path(
        user_id=payload.user_id,
        assessment=payload.assessment_results,
        user_goal=payload.user_goal,
    )
    return LearningPathResponse.model_validate(result)


@router.get("/{user_id}", response_model=LearningPathResponse)
async def get_learning_path(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
) -> LearningPathResponse:
    if user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to access this user's learning path",
        )

    service = LearningPathService(db)
    result = await service.get_learning_path(user_id=user_id)
    return LearningPathResponse.model_validate(result)


@router.put("/{user_id}/recalculate", response_model=LearningPathResponse)
async def recalculate_learning_path(
    user_id: UUID,
    payload: RecalculateLearningPathRequest,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
) -> LearningPathResponse:
    if user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to recalculate this user's learning path",
        )

    service = LearningPathService(db)
    result = await service.recalculate_learning_path(
        user_id=user_id,
        assessment=payload.assessment_results,
        user_goal=payload.user_goal,
    )
    return LearningPathResponse.model_validate(result)
