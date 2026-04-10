import logging
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.models.resume import Resume
from app.schemas.resume import (
    ResumeDetail,
    resume_to_detail,
)
from app.services.interview_service import ingest_keywords_and_generate
from app.services.nlp_parser import parse_resume
from app.services.pdf_extractor import extract_text
from app.utils.auth import get_current_user_id

router = APIRouter()
log = logging.getLogger(__name__)

MAX_BYTES = 10 * 1024 * 1024  # 10MB default


@router.post(
    "/upload",
    status_code=201,
    summary="Upload PDF resume",
)
async def upload_resume(
    file: UploadFile = File(..., description="Resume PDF file"),
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Upload and parse resume. Requires JWT authentication.
    The user_id is extracted from the authenticated JWT token.
    """

    try:
        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")

        file_bytes = await file.read()
        if len(file_bytes) > MAX_BYTES:
            raise HTTPException(status_code=413, detail="File too large")

        raw_text = extract_text(file_bytes, file.filename)
        if not raw_text.strip():
            raise HTTPException(status_code=422, detail="Could not extract text")

        parsed = parse_resume(raw_text)

        resume = Resume(
            user_id=str(user_id),
            filename=file.filename,
            raw_text=raw_text,
            file_size_kb=round(len(file_bytes) / 1024, 1),
            full_name=parsed.get("full_name"),
            email=parsed.get("email"),
            phone=parsed.get("phone"),
            location=parsed.get("location"),
            linkedin_url=parsed.get("linkedin_url"),
            github_url=parsed.get("github_url"),
            summary=parsed.get("summary"),
            skills=parsed.get("skills", []),
            experience=parsed.get("experience", []),
            education=parsed.get("education", []),
            certifications=parsed.get("certifications", []),
            projects=parsed.get("projects", []),
            languages=parsed.get("languages", []),
            achievements=parsed.get("achievements", []),
            experience_level=parsed.get("experience_level"),
            suggested_roles=parsed.get("suggested_roles", []),
            primary_tech_stack=parsed.get("primary_tech_stack", []),
            interview_topics=parsed.get("interview_topics", []),
            strength_areas=parsed.get("strength_areas", []),
            gap_areas=parsed.get("gap_areas", []),
            parse_status="success",
        )

        db.add(resume)
        await db.commit()
        await db.refresh(resume)

        # Trigger keyword ingestion + question generation
        keywords_to_ingest = resume.interview_topics or resume.skills
        if keywords_to_ingest:
            await ingest_keywords_and_generate(
                db,
                user_id=user_id,
                keywords=keywords_to_ingest[:5],  # limit for performance
            )

        return {
            "message": "Resume uploaded and parsed successfully",
            "user_id": str(user_id),
            "resume": resume_to_detail(resume),
        }

    except HTTPException:
        # Re-raise FastAPI exceptions directly
        raise

    except Exception as e:
        log.error(f"Upload failed: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/parse/{resume_id}",
    response_model=ResumeDetail,
    summary="Get parsed resume data",
)
async def get_parsed_resume(
    resume_id: str,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get resume data. User can only access their own resumes."""

    stmt = select(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == str(user_id),
    )

    result = await db.execute(stmt)
    resume = result.scalar_one_or_none()

    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    return resume_to_detail(resume)
