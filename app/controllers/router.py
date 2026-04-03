from fastapi import APIRouter

from app.controllers.routes.interview import router as interview_history_router
from app.controllers.routes.mock_interview import router as mock_router
from app.controllers.routes.practice import router as practice_router
from app.controllers.routes.resume import router as resume_router

api_router = APIRouter()

# Practice (Section 1)
api_router.include_router(practice_router, prefix="/v1")

# Mock Interview (Section 2) - start session, submit answer, feedback
api_router.include_router(mock_router, prefix="/v1")

# Interview History - history, replay, progress, delete, audio
api_router.include_router(interview_history_router)

# Integrated Modules
api_router.include_router(resume_router, prefix="/resume", tags=["Resume Parser"])