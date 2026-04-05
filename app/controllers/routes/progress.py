from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.schemas.progress_schema import (
    ProgressRecordRequest,
    ProgressRecordResponse,
    ModuleDetailsResponse,
    SummaryResponse,
)
from app.services.progress_service import ProgressService

router = APIRouter(prefix="/api/v1/progress", tags=["progress"])


@router.post("/record", response_model=ProgressRecordResponse)
async def record_progress(payload: ProgressRecordRequest, db: AsyncSession = Depends(get_db)) -> ProgressRecordResponse:
    svc = ProgressService(db)
    return await svc.record_progress(payload.user_id, payload.module, payload.topic, payload.subtopic, payload.is_correct, payload.time_spent_secs or 0)


@router.get("/{user_id}/summary", response_model=SummaryResponse)
async def get_summary(user_id: UUID, db: AsyncSession = Depends(get_db)) -> SummaryResponse:
    svc = ProgressService(db)
    return await svc.get_summary(str(user_id))


@router.get("/{user_id}/module/{module}", response_model=ModuleDetailsResponse)
async def get_module_details(user_id: UUID, module: str, db: AsyncSession = Depends(get_db)) -> ModuleDetailsResponse:
    svc = ProgressService(db)
    return await svc.get_module_details(str(user_id), module)


@router.get("/{user_id}/streaks")
async def get_streaks(user_id: UUID, db: AsyncSession = Depends(get_db)) -> dict:
    svc = ProgressService(db)
    return await svc.get_streaks(str(user_id))
