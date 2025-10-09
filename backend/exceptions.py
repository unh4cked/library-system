"""Custom exceptions and error handlers for the library system."""
from __future__ import annotations

from typing import Any

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from .logging_config import get_logger

logger = get_logger(__name__)


class LibraryException(Exception):
    """Base exception for library system."""
    
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: dict[str, Any] | None = None,
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ResourceNotFoundError(LibraryException):
    """Raised when a requested resource is not found."""
    
    def __init__(self, resource: str, identifier: int | str):
        super().__init__(
            message=f"{resource} با شناسه {identifier} یافت نشد",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"resource": resource, "id": identifier},
        )


class ResourceAlreadyExistsError(LibraryException):
    """Raised when trying to create a resource that already exists."""
    
    def __init__(self, resource: str, field: str, value: Any):
        super().__init__(
            message=f"{resource} با {field}='{value}' از قبل وجود دارد",
            status_code=status.HTTP_409_CONFLICT,
            details={"resource": resource, "field": field, "value": str(value)},
        )


class BusinessLogicError(LibraryException):
    """Raised when business logic validation fails."""
    
    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details,
        )


async def library_exception_handler(
    request: Request,
    exc: LibraryException,
) -> JSONResponse:
    """Handle custom library exceptions."""
    logger.warning(
        f"Library exception: {exc.message}",
        extra={"status_code": exc.status_code, "details": exc.details},
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.message,
            "type": exc.__class__.__name__,
            **exc.details,
        },
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Handle Pydantic validation errors."""
    logger.warning(f"Validation error: {exc.errors()}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "خطا در اعتبارسنجی داده‌های ورودی",
            "errors": exc.errors(),
        },
    )


async def integrity_exception_handler(
    request: Request,
    exc: IntegrityError,
) -> JSONResponse:
    """Handle database integrity errors."""
    logger.error(f"Database integrity error: {exc}", exc_info=True)
    
    # Parse common integrity errors
    error_msg = str(exc.orig) if hasattr(exc, "orig") else str(exc)
    
    if "UNIQUE constraint failed" in error_msg or "unique constraint" in error_msg.lower():
        message = "مقدار تکراری - این مورد از قبل وجود دارد"
    elif "FOREIGN KEY constraint failed" in error_msg:
        message = "ارجاع نامعتبر - شناسه مورد نظر وجود ندارد"
    else:
        message = "خطا در ثبت اطلاعات در پایگاه داده"
    
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": message},
    )


async def database_exception_handler(
    request: Request,
    exc: SQLAlchemyError,
) -> JSONResponse:
    """Handle general database errors."""
    logger.error(f"Database error: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "خطا در دسترسی به پایگاه داده"},
    )


async def general_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Handle all uncaught exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "خطای داخلی سرور",
            "type": exc.__class__.__name__,
        },
    )
