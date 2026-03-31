from fastapi import APIRouter

from app.controllers.routes.interview import router as interview_router
from app.controllers.routes.practice import router as practice_router
from app.controllers.routes.resume import router as resume_router

api_router = APIRouter()

api_router.include_router(practice_router, prefix="/v1")
api_router.include_router(interview_router, prefix="/v1")

# Integrated Modules
api_router.include_router(resume_router, prefix="/resume", tags=["Resume Parser"])
