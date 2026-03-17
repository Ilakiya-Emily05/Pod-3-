from fastapi import APIRouter

from app.controllers.routes import grammar_router, listening_router, reading_router

api_router = APIRouter()
api_router.include_router(reading_router)
api_router.include_router(listening_router)
api_router.include_router(grammar_router)
