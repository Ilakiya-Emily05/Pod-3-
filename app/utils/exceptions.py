import logging

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class ResumeParseError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message


class UnsupportedFileTypeError(Exception):
    def __init__(self, message: str = "Only PDF files are supported") -> None:
        self.message = message


class FileTooLargeError(Exception):
    def __init__(self, max_mb: int) -> None:
        self.message = f"File exceeds maximum allowed size of {max_mb}MB"


class ResumeNotFoundError(Exception):
    def __init__(self, resume_id: str) -> None:
        self.message = f"Resume not found: {resume_id}"


# ── FastAPI exception handlers ────────────────────────────────────────────────


async def resume_parse_error_handler(request: Request, exc: ResumeParseError):
    return JSONResponse(
        status_code=422,
        content={
            "error": "parse_failed",
            "message": exc.message,
        },
    )


async def unsupported_file_handler(request: Request, exc: UnsupportedFileTypeError):
    return JSONResponse(
        status_code=400,
        content={
            "error": "unsupported_file_type",
            "message": exc.message,
        },
    )


async def file_too_large_handler(request: Request, exc: FileTooLargeError):
    return JSONResponse(
        status_code=413,
        content={
            "error": "file_too_large",
            "message": exc.message,
        },
    )


async def not_found_handler(request: Request, exc: ResumeNotFoundError):
    return JSONResponse(
        status_code=404,
        content={
            "error": "not_found",
            "message": exc.message,
        },
    )


async def validation_error_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "error": "validation_error",
            "message": "Request validation failed",
            "detail": exc.errors(),
        },
    )


async def unhandled_error_handler(request: Request, exc: Exception):
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": "http_error",
                "message": exc.detail,
            },
        )

    logger.exception("Unhandled exception occurred during request processing")
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": "An unexpected error occurred. Please try again.",
        },
    )
