from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse, JSONResponse

from app.config.database import init_db
from app.config.settings import get_settings
from app.controllers.router import api_router


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Power Up API",
        description=(
            "Power Up async FastAPI backend — serving the mobile app and admin dashboard.\n\n"
            "**Docs:** `/docs` (Swagger UI) · `/redoc` (ReDoc) · `/openapi.json` (schema)"
        ),
        version="0.1.0",
        docs_url=None,    # served manually below so we can customise
        redoc_url=None,
        openapi_url="/openapi.json",
        contact={"name": "Power Up Engineering"},
        license_info={"name": "Proprietary"},
    )

    # ── CORS ────────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

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
    def custom_openapi() -> dict:
        if app.openapi_schema:
            return app.openapi_schema
        schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )
        schema["info"]["x-logo"] = {"url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"}
        app.openapi_schema = schema
        return schema

    app.openapi = custom_openapi  # type: ignore[method-assign]

    # ── Health check ─────────────────────────────────────────────────────────
    @app.get("/health", tags=["health"], summary="Liveness probe")
    async def health() -> JSONResponse:
        return JSONResponse({"status": "ok", "version": app.version})

    @app.on_event("startup")
    async def startup_event() -> None:
        await init_db()

    # ── Routers ───────────────────────────────────────────────────────────────
    app.include_router(api_router, prefix=settings.api_v1_prefix)

    return app


app = create_app()
