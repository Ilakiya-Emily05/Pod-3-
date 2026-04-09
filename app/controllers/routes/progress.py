from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.utils.auth import get_current_user_id
from app.schemas.progress_schema import (
    ProgressRecordRequest,
    ProgressRecordResponse,
    ModuleDetailsResponse,
    SummaryResponse,
)
from app.services.progress_service import ProgressService

router = APIRouter(prefix="/api/v1/progress", tags=["progress"])


@router.post("/record", response_model=ProgressRecordResponse)
async def record_progress(
    payload: ProgressRecordRequest,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
) -> ProgressRecordResponse:
    if payload.user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to modify this user's progress",
        )

    svc = ProgressService(db)
    return await svc.record_progress(
        str(current_user_id),
        payload.module,
        payload.topic,
        payload.subtopic,
        payload.is_correct,
        payload.time_spent_secs or 0,
    )


@router.get("/{user_id}/summary", response_model=SummaryResponse)
async def get_summary(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
) -> SummaryResponse:
    if user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to access this user's progress",
        )

    svc = ProgressService(db)
    return await svc.get_summary(str(user_id))


@router.get("/{user_id}/module/{module}", response_model=ModuleDetailsResponse)
async def get_module_details(
    user_id: UUID,
    module: str,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
) -> ModuleDetailsResponse:
    if user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to access this user's progress",
        )

    svc = ProgressService(db)
    return await svc.get_module_details(str(user_id), module)


@router.get("/{user_id}/streaks")
async def get_streaks(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
) -> dict:
    if user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to access this user's progress",
        )

    svc = ProgressService(db)
    return await svc.get_streaks(str(user_id))
