"""One error envelope for every failure, so the frontend only handles one shape:

    {"success": false, "error": {"code": "...", "message": "...", "details": ...}, "request_id": "..."}
"""
import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from .logging_config import request_id_var

logger = logging.getLogger("app.errors")


class AppError(Exception):
    status_code = 400
    code = "BAD_REQUEST"

    def __init__(self, message: str, details: Any = None):
        super().__init__(message)
        self.message = message
        self.details = details


class AuthError(AppError):
    status_code = 401
    code = "UNAUTHORIZED"


class InvalidFileError(AppError):
    status_code = 415
    code = "INVALID_FILE"


class FileTooLargeError(AppError):
    status_code = 413
    code = "FILE_TOO_LARGE"


class EmptyDocumentError(AppError):
    status_code = 422
    code = "NO_TEXT_FOUND"


class NotFoundError(AppError):
    status_code = 404
    code = "NOT_FOUND"


class LLMError(AppError):
    """The model call failed (timeout, throttling, endpoint down)."""
    status_code = 502
    code = "LLM_UPSTREAM_ERROR"


class LLMOutputError(AppError):
    """The model answered, but not with JSON that matches our schema (after a retry)."""
    status_code = 502
    code = "LLM_INVALID_OUTPUT"


def _envelope(status: int, code: str, message: str, details: Any = None) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content={
            "success": False,
            "error": {"code": code, "message": message, "details": details},
            "request_id": request_id_var.get(),
        },
        headers={"X-Request-ID": request_id_var.get()},
    )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(_: Request, exc: AppError):
        logger.warning("app_error", extra={"code": exc.code, "error": exc.message})
        return _envelope(exc.status_code, exc.code, exc.message, exc.details)

    @app.exception_handler(RequestValidationError)
    async def validation_handler(_: Request, exc: RequestValidationError):
        return _envelope(422, "VALIDATION_ERROR", "Request validation failed", exc.errors())

    @app.exception_handler(StarletteHTTPException)
    async def http_handler(_: Request, exc: StarletteHTTPException):
        return _envelope(exc.status_code, "HTTP_ERROR", str(exc.detail))

    @app.exception_handler(Exception)
    async def unhandled_handler(_: Request, exc: Exception):
        logger.exception("unhandled_error")
        return _envelope(500, "INTERNAL_ERROR", "Something went wrong. Quote the request_id when reporting it.")
