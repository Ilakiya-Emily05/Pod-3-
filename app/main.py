from typing import Any, AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse, JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from app.config.database import init_db
from app.config.settings import get_settings
from app.controllers.router import api_router
from app.utils.exceptions import (
    FileTooLargeError,
    ResumeNotFoundError,
    ResumeParseError,
    UnsupportedFileTypeError,
    file_too_large_handler,
    not_found_handler,
    resume_parse_error_handler,
    unhandled_error_handler,
    unsupported_file_handler,
    validation_error_handler,
)

# ── Rate Limiter ─────────────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address, default_limits=["30/minute"])


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup: Initialize database (run migrations/create tables)
    await init_db()
    yield
    # Shutdown logic if needed


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Power Up Unified API",
        description=(
            "Unified FastAPI backend integrating Interview Coach and Resume Parser modules.\n\n"
            "**Docs:** `/docs` (Swagger UI) · `/redoc` (ReDoc) · `/openapi.json` (schema)"
        ),
        version="1.0.0",
        docs_url=None,  # served manually below so we can customise
        redoc_url=None,
        openapi_url="/openapi.json",
        contact={"name": "Power Up Engineering"},
        license_info={"name": "Proprietary"},
        lifespan=lifespan,
    )

    # ── Middleware ──────────────────────────────────────────────────────────
    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Exception Handlers ──────────────────────────────────────────────────
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_exception_handler(ResumeParseError, resume_parse_error_handler)
    app.add_exception_handler(UnsupportedFileTypeError, unsupported_file_handler)
    app.add_exception_handler(FileTooLargeError, file_too_large_handler)
    app.add_exception_handler(ResumeNotFoundError, not_found_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(Exception, unhandled_error_handler)

    # ── Swagger UI ───────────────────────────────────────────────────────────
    @app.get("/docs", include_in_schema=False)
    async def swagger_ui() -> HTMLResponse:
        return get_swagger_ui_html(
            openapi_url="/openapi.json",
            title="Power Up API — Swagger UI",
            swagger_favicon_url="https://fastapi.tiangolo.com/img/favicon.png",
        )

    # ── ReDoc ────────────────────────────────────────────────────────────────
    @app.get("/redoc", include_in_schema=False)
    async def redoc_ui() -> HTMLResponse:
        return get_redoc_html(
            openapi_url="/openapi.json",
            title="Power Up API — ReDoc",
            redoc_favicon_url="https://fastapi.tiangolo.com/img/favicon.png",
        )

    # ── OpenAPI schema override (adds servers block) ─────────────────────────
    def custom_openapi() -> dict[str, Any]:
        if app.openapi_schema:
            return app.openapi_schema
        schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )
        schema["info"]["x-logo"] = {
            "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"
        }
        app.openapi_schema = schema
        return schema

    app.openapi = custom_openapi  # type: ignore[method-assign]

    # ── Health check ─────────────────────────────────────────────────────────
    @app.get("/health", tags=["health"], summary="Liveness probe")
    async def health() -> JSONResponse:
        return JSONResponse({"status": "ok", "version": app.version})

    # ── Routers ───────────────────────────────────────────────────────────────
    app.include_router(api_router, prefix=settings.api_v1_prefix)

    return app


app = create_app()
