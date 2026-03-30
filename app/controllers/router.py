from fastapi import APIRouter

from app.controllers.routes.admin import router as admin_router
from app.controllers.routes.auth import router as auth_router
from app.controllers.routes.grammar import router as grammar_router
from app.controllers.routes.listening import router as listening_router
from app.controllers.routes.onboarding import router as onboarding_router
from app.controllers.routes.progress import router as progress_router
from app.controllers.routes.reading import router as reading_router
from app.routes. audio_route import router as audio_router
from app.routes.listening_route import router as listening_route
from app.routes.listening_test_route import router as listening_test_router
from app.routes.question_route import router as question_router

api_router = APIRouter()
api_router.include_router(admin_router)
api_router.include_router(auth_router)
api_router.include_router(onboarding_router)
api_router.include_router(reading_router)
api_router.include_router(grammar_router)
api_router.include_router(listening_router)
api_router.include_router(progress_router)


api_router.include_router(audio_router)
api_router.include_router(listening_route)
api_router.include_router(listening_test_router)
api_router.include_router(question_router)
