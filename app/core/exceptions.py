"""
Custom exceptions for the application.
Follows SOLID principles with specific exception types.
"""


class PIKAMemoryException(Exception):
    """Base exception for all PIKA Memory System errors."""
    pass


class MemoryNotFoundError(PIKAMemoryException):
    """Raised when a memory is not found."""
    pass


class JobNotFoundError(PIKAMemoryException):
    """Raised when a job is not found."""
    pass


class CacheError(PIKAMemoryException):
    """Raised when cache operations fail."""
    pass


class RepositoryError(PIKAMemoryException):
    """Raised when repository operations fail."""
    pass


class ServiceError(PIKAMemoryException):
    """Raised when service operations fail."""
    pass


class ValidationError(PIKAMemoryException):
    """Raised when input validation fails."""
    pass


class ExternalServiceError(PIKAMemoryException):
    """Raised when external service calls fail."""
    pass


class Mem0Error(ExternalServiceError):
    """Raised when Mem0 API calls fail."""
    pass


class DatabaseError(RepositoryError):
    """Raised when database operations fail."""
    pass


class MessageQueueError(PIKAMemoryException):
    """Raised when message queue operations fail."""
    pass

