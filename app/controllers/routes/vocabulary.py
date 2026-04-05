from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from typing import List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas import vocabulary as vocab_schemas
from app.services.vocabulary_service import VocabularyService
from app.config.database import get_session

router = APIRouter(prefix="/api/v1/vocabulary", tags=["vocabulary"])


@router.get("/words/{user_id}", response_model=vocab_schemas.WordsResponse)
async def get_due_words(user_id: UUID, limit: int = 20, db: AsyncSession = Depends(get_session)):
    svc = VocabularyService(db)
    items = await svc.get_due_words(user_id, limit=limit)
    words = []
    for uv, vw in items:
        words.append(vocab_schemas.WordItem(
            word_id=vw.id,
            word=vw.word,
            definition=vw.definition,
            part_of_speech=vw.part_of_speech,
            industry=vw.industry,
            difficulty=vw.difficulty,
            example_sentence=vw.example_sentence,
            pronunciation_audio_url=vw.pronunciation_audio_url,
            last_reviewed=uv.last_reviewed,
            retention_score=uv.easiness,
            next_review_due=uv.next_review_date,
        ))

    return vocab_schemas.WordsResponse(session_id=UUID(int=0), words=words, total_words_in_session=len(words))


@router.post("/response", response_model=vocab_schemas.ResponseResult)
async def record_response(payload: vocab_schemas.ResponseRecord, db: AsyncSession = Depends(get_session)):
    svc = VocabularyService(db)
    result = await svc.record_response(payload.user_id, payload.word_id, payload.response_quality, payload.response_time_ms)
    return vocab_schemas.ResponseResult(
        word_id=payload.word_id,
        new_retention_score=result["new_retention_score"],
        next_review_date=result["next_review_date"],
        interval_days=result["interval_days"],
        feedback="ok",
    )


@router.get("/lists", response_model=List[vocab_schemas.VocabularyListItem])
async def list_lists(db: AsyncSession = Depends(get_session)):
    svc = VocabularyService(db)
    lists = await svc.list_word_lists()
    out = []
    for l in lists:
        out.append(vocab_schemas.VocabularyListItem(
            list_id=l.id,
            name=l.name,
            industry=l.industry,
            difficulty=l.difficulty,
            word_count=l.word_count,
            description=l.description,
        ))
    return out


@router.post("/lists/{list_id}/start", response_model=vocab_schemas.StartListResult)
async def start_list(list_id: UUID, user_id: UUID, db: AsyncSession = Depends(get_session)):
    svc = VocabularyService(db)
    count = await svc.start_list_for_user(list_id, user_id)
    return vocab_schemas.StartListResult(list_id=list_id, started=count > 0)
