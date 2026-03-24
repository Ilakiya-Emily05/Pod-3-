
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from pydantic import BaseModel

from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.core.database import init_db, check_db
from app.core.exceptions import (
    ResumeParseError,        resume_parse_error_handler,
    UnsupportedFileTypeError, unsupported_file_handler,
    FileTooLargeError,       file_too_large_handler,
    ResumeNotFoundError,     not_found_handler,
    validation_error_handler,
    unhandled_error_handler,
)
from app.routes.resume import router as resume_router

setup_logging()
log = get_logger(__name__)


class HealthResponse(BaseModel):
    api:      str
    database: str
    env:      str


limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.RATE_LIMIT_PER_MINUTE}/minute"],
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info(f"Startup — env={settings.APP_ENV}")
    init_db()
    yield
    log.info("Shutdown")


app = FastAPI(
    title="ResumeVault API",
    version="1.0.0",
    description="Upload resume PDF → NLP parse → store in DB",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(RateLimitExceeded,        _rate_limit_exceeded_handler)
app.add_exception_handler(ResumeParseError,         resume_parse_error_handler)
app.add_exception_handler(UnsupportedFileTypeError, unsupported_file_handler)
app.add_exception_handler(FileTooLargeError,        file_too_large_handler)
app.add_exception_handler(ResumeNotFoundError,      not_found_handler)
app.add_exception_handler(RequestValidationError,   validation_error_handler)
app.add_exception_handler(Exception,                unhandled_error_handler)

app.include_router(resume_router, prefix="/api/resumes", tags=["resumes"])


@app.get("/", include_in_schema=False)
def root():
    return {"message": "ResumeVault API", "docs": "/docs", "health": "/health"}


@app.get("/health", response_model=HealthResponse, tags=["system"])
def health():
    return HealthResponse(
        api="ok",
        database="ok" if check_db() else "unreachable",
        env=settings.APP_ENV,
    )
