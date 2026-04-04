from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError


class ResumeParseError(Exception):
    def __init__(self, message: str):
        self.message = message


class UnsupportedFileTypeError(Exception):
    def __init__(self, message: str = "Only PDF files are supported"):
        self.message = message


class FileTooLargeError(Exception):
    def __init__(self, max_mb: int):
        self.message = f"File exceeds maximum allowed size of {max_mb}MB"


class ResumeNotFoundError(Exception):
    def __init__(self, resume_id: str):
        self.message = f"Resume not found: {resume_id}"


# ── FastAPI exception handlers ────────────────────────────────────────────────

async def resume_parse_error_handler(request: Request, exc: ResumeParseError):
    return JSONResponse(status_code=422, content={
        "error": "parse_failed",
        "message": exc.message,
    })


async def unsupported_file_handler(request: Request, exc: UnsupportedFileTypeError):
    return JSONResponse(status_code=400, content={
        "error": "unsupported_file_type",
        "message": exc.message,
    })


async def file_too_large_handler(request: Request, exc: FileTooLargeError):
    return JSONResponse(status_code=413, content={
        "error": "file_too_large",
        "message": exc.message,
    })


async def not_found_handler(request: Request, exc: ResumeNotFoundError):
    return JSONResponse(status_code=404, content={
        "error": "not_found",
        "message": exc.message,
    })


async def validation_error_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={
        "error": "validation_error",
        "message": "Request validation failed",
        "detail": [
            {
                "loc": list(e.get("loc", [])),
                "msg": str(e.get("msg", "")),
                "type": str(e.get("type", "")),
            }
            for e in exc.errors()
        ],
    })


async def unhandled_error_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={
        "error": "internal_server_error",
        "message": "An unexpected error occurred. Please try again.",
    })
