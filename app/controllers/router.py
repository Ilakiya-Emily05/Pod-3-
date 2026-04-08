from fastapi import APIRouter

from app.controllers.routes import (
    auth_router,
    behav_assessment_router,
    grammar_router,
    listening_router,
    onboarding_router,
    reading_router,
    sentence_framing_router,
)
from app.controllers.routes.admin import router as admin_router
from app.controllers.routes.analytics import router as analytics_router
from app.controllers.routes.auth import router as auth_router
from app.controllers.routes.behav_assessment_routes import router as behav_assessment_router
from app.controllers.routes.grammar import router as grammar_router
from app.controllers.routes.listening import router as listening_assessment_router
from app.controllers.routes.onboarding import router as onboarding_router
from app.controllers.routes.progress import router as progress_router
from app.controllers.routes.reading import router as reading_router
from app.controllers.routes.practice import router as practice_router
from app.controllers.routes.resume import router as resume_router
from app.routes.audio_route import router as audio_router
from app.routes.listening_route import router as listening_module_router
from app.routes.listening_test_route import router as listening_test_router
from app.routes.question_route import router as question_router

api_router = APIRouter()
api_router.include_router(admin_router)
api_router.include_router(analytics_router)
api_router.include_router(auth_router)
api_router.include_router(onboarding_router)
api_router.include_router(reading_router)
api_router.include_router(grammar_router)
api_router.include_router(listening_assessment_router)
api_router.include_router(progress_router)
api_router.include_router(behav_assessment_router)
api_router.include_router(practice_router, prefix="/v1")
api_router.include_router(resume_router, prefix="/resume", tags=["Resume Parser"])


api_router.include_router(audio_router)
api_router.include_router(listening_module_router)
api_router.include_router(listening_test_router)
api_router.include_router(question_router)
api_router.include_router(sentence_framing_router)
