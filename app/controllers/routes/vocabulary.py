from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.config.database import get_session
from app.services.vocabulary_service import VocabularyService
from app.schemas.vocabulary_schema import (
    WordsResponse,
    WordItem,
    ResponseRecord,
    ResponseResult,
    VocabularyStats,
)

router = APIRouter(
    prefix="/api/v1/vocabulary",
    tags=["vocabulary"]
)

@router.get("/words/{user_id}", response_model=WordsResponse)
async def get_words(
    user_id: UUID,
    limit: int = 10,
    db: AsyncSession = Depends(get_session),
):
    service = VocabularyService(db)

    session = await service.create_session(user_id)

    items = await service.get_words(user_id, limit)

    words = []

    for uv, vw in items:
        words.append(
            WordItem(
                word_id=vw.word_id,
                word=vw.word,
                definition=vw.definition,
                cefr_level=vw.cefr_level,
                example_sentence=vw.example_sentence,
                last_reviewed_at=uv.last_reviewed_at,
                retention_score=uv.retention_score,
                next_review_due=uv.next_review_date,
            )
        )

    return WordsResponse(
        session_id=session.session_id,
        words=words,
        total_words_in_session=len(words),
    )

@router.post("/response", response_model=ResponseResult)
async def record_response(
    payload: ResponseRecord,
    db: AsyncSession = Depends(get_session),
):
    service = VocabularyService(db)

    result = await service.record_response(
        session_id=payload.session_id,
        user_id=payload.user_id,
        word_id=payload.word_id,
        response=payload.response,
    )

    return ResponseResult(
        word_id=result["word_id"],
        new_retention_score=result["new_retention_score"],
        next_review_date=result["next_review_date"],
        interval_days=result["interval_days"],
        feedback=result["feedback"],
    )

@router.get("/stats/{user_id}", response_model=VocabularyStats)
async def get_stats(
    user_id: UUID,
    db: AsyncSession = Depends(get_session),
):
    service = VocabularyService(db)

    stats = await service.get_stats(user_id)

    return VocabularyStats(**stats)