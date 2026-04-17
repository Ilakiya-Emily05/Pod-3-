from __future__ import annotations

import uuid
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.schemas.assessment_session import (
    AssessmentSessionCreate,
    AssessmentSessionRead,
    AssessmentSessionResult,
)
from app.services.assessment_session_service import AssessmentSessionService
from app.models.assessment_session import AssessmentSection
from app.utils.auth import get_current_user_id

router = APIRouter(prefix="/assessment-sessions", tags=["Assessment Sessions"])
logger = logging.getLogger(__name__)


@router.post(
    "/",
    response_model=AssessmentSessionRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_assessment_session(
    payload: AssessmentSessionCreate,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> AssessmentSessionRead:
    try:
        session = await AssessmentSessionService.create_session(
            db=db,
            user_id=user_id,
            session_type=payload.session_type,
        )
        return session
    except Exception as exc:
        logger.exception("Failed to create assessment session", exc_info=exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while creating assessment session",
        ) from exc


@router.get(
    "/{session_id}",
    response_model=AssessmentSessionRead,
    status_code=status.HTTP_200_OK,
)
async def get_assessment_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> AssessmentSessionRead:
    try:
        session = await AssessmentSessionService.get_session(db=db, session_id=session_id)

        if session.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not allowed to access this session",
            )

        return session
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception(
            "Failed to fetch assessment session %s", session_id, exc_info=exc
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while fetching assessment session",
        ) from exc


@router.post(
    "/{session_id}/sections/{section}/submit",
    response_model=AssessmentSessionRead,
    status_code=status.HTTP_200_OK,
)
async def submit_assessment_section(
    session_id: uuid.UUID,
    section: AssessmentSection,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> AssessmentSessionRead:
    try:
        session = await AssessmentSessionService.get_session(db=db, session_id=session_id)

        if session.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not allowed to modify this session",
            )

        updated_session = await AssessmentSessionService.submit_section(
            db=db,
            session_id=session_id,
            section=section,
        )
        return updated_session
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception(
            "Failed to submit section %s for session %s",
            section,
            session_id,
            exc_info=exc,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while submitting assessment section",
        ) from exc


@router.get(
    "/{session_id}/result",
    response_model=AssessmentSessionResult,
    status_code=status.HTTP_200_OK,
)
async def get_assessment_session_result(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> AssessmentSessionResult:
    try:
        session = await AssessmentSessionService.get_session(db=db, session_id=session_id)

        if session.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not allowed to access this session result",
            )

        result = await AssessmentSessionService.get_result(db=db, session_id=session_id)

        return AssessmentSessionResult(
            id=result.id,
            user_id=result.user_id,
            session_type=result.session_type,
            status=result.status,
            current_section=result.current_section,
            composite_cefr_result=result.composite_cefr_result,
            started_at=result.started_at,
            completed_at=result.completed_at,
            section_scores=getattr(result, "section_scores", {}) or {},
        )
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception(
            "Failed to fetch result for assessment session %s", session_id, exc_info=exc
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while fetching assessment session result",
        ) from exc