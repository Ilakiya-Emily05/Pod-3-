from fastapi import APIRouter

from app.controllers.routes.auth import router as auth_router
from app.controllers.routes.grammar import router as grammar_router
from app.controllers.routes.listening import router as listening_router
from app.controllers.routes.onboarding import router as onboarding_router
from app.controllers.routes.reading import router as reading_router
from app.controllers.routes.auth import router as auth_router
from app.controllers.routes.test import router as tests_router 
from app.controllers.routes.passage import router as passage_router
from app.controllers.routes.progress import router as progress_router
from app.controllers.routes.behav_assessment_routes import router as behav_assessment_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(progress_router)
api_router.include_router(onboarding_router)
api_router.include_router(behav_assessment_router)
#api_router.include_router(reading_router)
#api_router.include_router(grammar_router)
#api_router.include_router(listening_router)
api_router.include_router(tests_router)
api_router.include_router(passage_router)
