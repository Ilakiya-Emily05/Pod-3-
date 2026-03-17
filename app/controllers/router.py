from fastapi import APIRouter

from app.controllers.routes.auth import router as auth_router

api_router = APIRouter()
api_router.include_router(auth_router)
