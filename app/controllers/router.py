from fastapi import APIRouter

# Import all routers from routes directory
from app.controllers.routes.admin import router as admin_router
from app.controllers.routes.analytics import router as analytics_router
from app.controllers.routes.auth import router as auth_router
from app.controllers.routes.behav_assessment_routes import router as behav_assessment_router
from app.controllers.routes.grammar import router as grammar_router
from app.controllers.routes.interview import router as interview_router
from app.controllers.routes.learning_path import router as learning_path_router
from app.controllers.routes.listening import router as listening_router
from app.controllers.routes.listening1 import router as listening1_router
from app.controllers.routes.listening_test import router as listening_test_router
from app.controllers.routes.onboarding import router as onboarding_router
from app.controllers.routes.passage import router as passage_router
from app.controllers.routes.practice import router as practice_router
from app.controllers.routes.progress import router as progress_router
from app.controllers.routes.progress1 import router as progress1_router
from app.controllers.routes.pronun_profile import router as pronun_profile_router
from app.controllers.routes.reading import router as reading_router
from app.controllers.routes.recommendations import router as recommendations_router
from app.controllers.routes.resume import router as resume_router
from app.controllers.routes.sentence_framing import router as sentence_framing_router
from app.controllers.routes.test import router as tests_router
from app.controllers.routes.vocabulary import router as vocabulary_router
from app.controllers.routes.assessment_session import router as assessment_session_router
from app.controllers.routes.question import router as question_router

# Import routers from the root routes directory (Pod 1/2)
from app.routes.audio_route import router as audio_router
from app.routes.listening_route import router as listening_module_router
from app.routes.listening_test_route import router as listening_test_module_router
from app.routes.question_route import router as question_module_router

api_router = APIRouter()

# Register all routers
api_router.include_router(admin_router)
api_router.include_router(analytics_router)
api_router.include_router(auth_router)
api_router.include_router(onboarding_router)
api_router.include_router(reading_router)
api_router.include_router(grammar_router)

# Listening and Progress
api_router.include_router(listening_router)
api_router.include_router(listening1_router)
api_router.include_router(listening_test_router)
api_router.include_router(progress_router)
api_router.include_router(progress1_router)

# Assessment and Learning
api_router.include_router(behav_assessment_router)
api_router.include_router(assessment_session_router)
api_router.include_router(learning_path_router)
api_router.include_router(recommendations_router)

# General modules
api_router.include_router(tests_router)
api_router.include_router(passage_router)
api_router.include_router(vocabulary_router)
api_router.include_router(pronun_profile_router)
api_router.include_router(question_router)

# Audio and Listening (Pod 1/2)
api_router.include_router(audio_router)
api_router.include_router(listening_module_router)
api_router.include_router(listening_test_module_router)
api_router.include_router(question_module_router)

# Pod 3 / Specialized Routes (Versioned)
api_router.include_router(practice_router, prefix="/v1")
api_router.include_router(interview_router, prefix="/v1")
api_router.include_router(resume_router, prefix="/v1", tags=["Resume Parser"])
api_router.include_router(sentence_framing_router)
