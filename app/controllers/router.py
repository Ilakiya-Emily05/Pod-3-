import logging

from fastapi import APIRouter

from app.controllers.routes.admin import router as admin_router
from app.controllers.routes.audio import router as audio_router
from app.controllers.routes.auth import router as auth_router
from app.controllers.routes.behav_assessment_routes import router as behav_assessment_router
from app.controllers.routes.grammar import router as grammar_router
from app.controllers.routes.listening import router as listening_router
from app.controllers.routes.listening1 import router as listening1_router
from app.controllers.routes.listening_test import router as listening_test_router
from app.controllers.routes.onboarding import router as onboarding_router
from app.controllers.routes.practice import router as practice_router
from app.controllers.routes.progress import router as progress_router
from app.controllers.routes.progress1 import router as progress1_router
from app.controllers.routes.pronun_profile import router as pronun_profile_router
from app.controllers.routes.question import router as question_router
from app.controllers.routes.reading import router as reading_router
from app.controllers.routes.recommendations import router as recommendations_router

api_router = APIRouter()

api_router.include_router(admin_router)
api_router.include_router(analytics_router)
api_router.include_router(auth_router)
api_router.include_router(onboarding_router)
api_router.include_router(reading_router)
api_router.include_router(grammar_router)
api_router.include_router(listening_assessment_router)
api_router.include_router(progress_router)
api_router.include_router(pronun_profile_router)
api_router.include_router(question_router)
api_router.include_router(recommendations_router)
api_router.include_router(audio_router)
api_router.include_router(listening1_router)
api_router.include_router(progress1_router)
api_router.include_router(listening_test_router)
