"""Centralized error types and FastAPI exception handlers."""

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from apps.api.app.core.logging import emit


class MoneyballError(Exception):
    """Base domain error carrying an HTTP status and machine code."""

    code = "moneyball_error"

    def __init__(self, message: str, *, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class NotFoundError(MoneyballError):
    code = "not_found"

    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(message, status_code=404)


class ConflictError(MoneyballError):
    code = "conflict"

    def __init__(self, message: str = "Conflict") -> None:
        super().__init__(message, status_code=409)


class UnauthorizedError(MoneyballError):
    code = "unauthorized"

    def __init__(self, message: str = "Authentication required") -> None:
        super().__init__(message, status_code=401)


class ForbiddenError(MoneyballError):
    code = "forbidden"

    def __init__(self, message: str = "Forbidden") -> None:
        super().__init__(message, status_code=403)


class ValidationError(MoneyballError):
    code = "validation_error"

    def __init__(self, message: str = "Validation failed") -> None:
        super().__init__(message, status_code=422)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(MoneyballError)
    async def moneyball_error_handler(request: Request, exc: MoneyballError) -> JSONResponse:
        emit("api.error", exc.message, path=str(request.url.path), code=exc.code)
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.code, "message": exc.message}},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        emit("api.error", "validation failed", path=str(request.url.path))
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "code": "validation_error",
                    "message": "Request validation failed",
                    "details": exc.errors()[:10],
                }
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_handler(request: Request, exc: Exception) -> JSONResponse:
        emit("api.error", str(exc), path=str(request.url.path), unhandled=True)
        return JSONResponse(
            status_code=500,
            content={"error": {"code": "internal_error", "message": "Internal server error"}},
        )