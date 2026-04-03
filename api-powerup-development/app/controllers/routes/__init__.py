from app.controllers.routes.auth import router as auth_router
from app.controllers.routes.grammar import router as grammar_router
from app.controllers.routes.listening import router as listening_router
from app.controllers.routes.onboarding import router as onboarding_router
from app.controllers.routes.reading import router as reading_router

__all__ = [
    "auth_router",
    "grammar_router",
    "listening_router",
    "onboarding_router",
    "reading_router",
]
