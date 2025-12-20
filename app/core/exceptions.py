"""
Custom Exceptions

Domain-agnostic exceptions for the application.
"""

from typing import Optional, Dict, Any


class AppException(Exception):
    """Base application exception"""
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(AppException):
    """Input validation error"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=400, details=details)


class NotFoundError(AppException):
    """Resource not found error"""
    
    def __init__(self, resource: str, identifier: str):
        message = f"{resource} with id '{identifier}' not found"
        super().__init__(message, status_code=404)


class UnauthorizedError(AppException):
    """Authentication/Authorization error"""
    
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message, status_code=401)


class ForbiddenError(AppException):
    """Permission denied error"""
    
    def __init__(self, message: str = "Forbidden"):
        super().__init__(message, status_code=403)


class RateLimitError(AppException):
    """Rate limit exceeded error"""
    
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, status_code=429)


class InternalServerError(AppException):
    """Internal server error"""
    
    def __init__(self, message: str = "Internal server error"):
        super().__init__(message, status_code=500)


class ServiceUnavailableError(AppException):
    """External service unavailable"""
    
    def __init__(self, service: str, message: Optional[str] = None):
        msg = message or f"Service '{service}' is currently unavailable"
        super().__init__(msg, status_code=503)

