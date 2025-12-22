"""
Error handling middleware for consistent error responses.
"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging import get_logger
from app.core.exceptions import (
    PIKAMemoryException,
    MemoryNotFoundError,
    JobNotFoundError,
    ValidationError,
    ServiceError,
)

logger = get_logger(__name__)


async def exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Global exception handler.
    
    Args:
        request: FastAPI request
        exc: Exception instance
        
    Returns:
        JSON error response
    """
    request_id = request.headers.get("X-Request-ID", "unknown")
    
    # Handle custom exceptions
    if isinstance(exc, JobNotFoundError):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "status": "error",
                "error_code": "JOB_NOT_FOUND",
                "message": str(exc),
                "request_id": request_id,
            },
        )
    
    if isinstance(exc, MemoryNotFoundError):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "status": "error",
                "error_code": "MEMORY_NOT_FOUND",
                "message": str(exc),
                "request_id": request_id,
            },
        )
    
    if isinstance(exc, ValidationError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "status": "error",
                "error_code": "VALIDATION_ERROR",
                "message": str(exc),
                "request_id": request_id,
            },
        )
    
    if isinstance(exc, ServiceError):
        logger.error(f"Service error: {exc}, request_id={request_id}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "error_code": "SERVICE_ERROR",
                "message": "Internal server error",
                "request_id": request_id,
            },
        )
    
    # Handle FastAPI/Starlette exceptions
    if isinstance(exc, StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "status": "error",
                "error_code": "HTTP_ERROR",
                "message": exc.detail,
                "request_id": request_id,
            },
        )
    
    if isinstance(exc, RequestValidationError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "status": "error",
                "error_code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "errors": exc.errors(),
                "request_id": request_id,
            },
        )
    
    # Handle unexpected exceptions
    logger.error(f"Unexpected error: {exc}, request_id={request_id}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "error_code": "INTERNAL_ERROR",
            "message": "Internal server error",
            "request_id": request_id,
        },
    )

