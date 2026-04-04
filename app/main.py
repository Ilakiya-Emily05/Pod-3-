from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.exceptions import RequestValidationError

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from contextlib import asynccontextmanager

from fastapi.responses import JSONResponse
import json

class SafeJSONResponse(JSONResponse):
    def render(self, content) -> bytes:
        return json.dumps(
            content,
            default=lambda o: str(o) if not isinstance(o, (int, float, bool, type(None))) else o,
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")

from app.config.database import engine
from app.utils.exceptions import (
    ResumeParseError, resume_parse_error_handler,
    UnsupportedFileTypeError, unsupported_file_handler,
    FileTooLargeError, file_too_large_handler,
    ResumeNotFoundError, not_found_handler,
    validation_error_handler,
    unhandled_error_handler,
)

# ── Rate Limiter ─────────────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address, default_limits=["30/minute"])


# ── Lifespan (Import models here to avoid circular imports) ──────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Register all models with SQLAlchemy MetaData
    # This ensures tables are registered exactly once at app startup
    # The register_models() function is idempotent and safe to call multiple times
    from app.models._register import register_models
    register_models()
    yield
    # Shutdown logic if needed


def create_app() -> FastAPI:
    app = FastAPI(
        default_response_class=SafeJSONResponse,
        title="Power Up Unified API",
        description=(
            "Unified FastAPI backend integrating Resume Parser and Interview Coach modules.\n\n"
            "**Docs:** `/docs` (Swagger UI) · `/redoc` (ReDoc) · `/openapi.json` (schema)"
        ),
        version="1.0.0",
        docs_url=None,
        redoc_url=None,
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # ── Middleware ──────────────────────────────────────────────────────────
    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
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

    # ── Swagger UI ──────────────────────────────────────────────────────────
    @app.get("/docs", include_in_schema=False)
    async def swagger_ui() -> HTMLResponse:
        return get_swagger_ui_html(
            openapi_url="/openapi.json",
            title="Power Up API — Swagger UI",
            swagger_favicon_url="https://fastapi.tiangolo.com/img/favicon.png",
        )

    # ── ReDoc ───────────────────────────────────────────────────────────────
    @app.get("/redoc", include_in_schema=False)
    async def redoc_ui() -> HTMLResponse:
        return get_redoc_html(
            openapi_url="/openapi.json",
            title="Power Up API — ReDoc",
            redoc_favicon_url="https://fastapi.tiangolo.com/img/favicon.png",
        )

    # ── OpenAPI schema override ─────────────────────────────────────────────
    def custom_openapi() -> dict:
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

    app.openapi = custom_openapi

    # ── Health check ────────────────────────────────────────────────────────
    @app.get("/health", tags=["health"], summary="Liveness probe")
    async def health() -> JSONResponse:
        return JSONResponse({"status": "ok", "version": app.version})

    # ── Routers ─────────────────────────────────────────────────────────────
    from app.controllers.router import api_router
    app.include_router(api_router, prefix="/api")

    return app


app = create_app()