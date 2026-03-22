import logging
import uuid
from fastapi import APIRouter, Depends, UploadFile, File, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.config.database import get_db
from app.models.resume import Resume
from app.schemas.resume import (
    resume_to_detail,
    resume_to_summary,
)
from app.services.pdf_extractor import extract_text
from app.services.nlp_parser import parse_resume
from app.config.settings import settings
from app.services.interview_service import ingest_keywords_and_generate

router = APIRouter()
log    = logging.getLogger(__name__)

MAX_BYTES = 10 * 1024 * 1024 # 10MB default


@router.post(
    "/upload",
    status_code=201,
    summary="Upload PDF resume",
)
async def upload_resume(
    user_id: str | None = None,
    file: UploadFile = File(..., description="Resume PDF file"),
    db:   AsyncSession = Depends(get_db),
):
    """
    Upload and parse. Generates a unique user_id if not provided,
    ensuring safe concurrency for multiple users.
    """
    if not user_id:
        user_id = str(uuid.uuid4())

    try:
        if not file.filename.lower().endswith(".pdf"):
            return JSONResponse(status_code=400, content={"error": "Only PDF files are supported"})

        file_bytes = await file.read()
        if len(file_bytes) > MAX_BYTES:
            return JSONResponse(status_code=413, content={"error": "File too large"})

        raw_text = extract_text(file_bytes, file.filename)
        if not raw_text.strip():
            return JSONResponse(status_code=422, content={"error": "Could not extract text"})

        parsed = parse_resume(raw_text)

        resume = Resume(
            user_id            = user_id,
            filename           = file.filename,
            raw_text           = raw_text,
            file_size_kb       = round(len(file_bytes) / 1024, 1),
            full_name          = parsed.get("full_name"),
            email              = parsed.get("email"),
            phone              = parsed.get("phone"),
            location           = parsed.get("location"),
            linkedin_url       = parsed.get("linkedin_url"),
            github_url         = parsed.get("github_url"),
            summary            = parsed.get("summary"),
            skills             = parsed.get("skills", []),
            experience         = parsed.get("experience", []),
            education          = parsed.get("education", []),
            certifications     = parsed.get("certifications", []),
            projects           = parsed.get("projects", []),
            languages          = parsed.get("languages", []),
            achievements       = parsed.get("achievements", []),
            experience_level   = parsed.get("experience_level"),
            suggested_roles    = parsed.get("suggested_roles", []),
            primary_tech_stack = parsed.get("primary_tech_stack", []),
            interview_topics   = parsed.get("interview_topics", []),
            strength_areas     = parsed.get("strength_areas", []),
            gap_areas          = parsed.get("gap_areas", []),
            parse_status       = "success",
        )
        db.add(resume)
        await db.commit()
        await db.refresh(resume)

        # TRIGGER UNIFIED FLOW: Ingest keywords for testing
        # We use interview_topics or skills for question generation
        keywords_to_ingest = resume.interview_topics or resume.skills
        if keywords_to_ingest:
            # TRIGGER UNIFIED FLOW: Ingest keywords for testing
            await ingest_keywords_and_generate(db, user_id=user_id, keywords=keywords_to_ingest[:5]) # limit to 5 main topics for performance

        return {
            "message": "Resume uploaded and parsed successfully",
            "user_id": user_id,
            "resume":  resume_to_detail(resume),
        }

    except Exception as e:
        log.error(f"Upload failed: {e}", exc_info=True)
        await db.rollback()
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/parse/{resume_id}", summary="Get parsed resume data")
async def get_parsed_resume(resume_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(Resume).filter(Resume.id == resume_id)
    result = await db.execute(stmt)
    resume = result.scalar_one_or_none()
    
    if not resume:
        return JSONResponse(status_code=404, content={"error": "Resume not found"})
    return resume_to_detail(resume)



