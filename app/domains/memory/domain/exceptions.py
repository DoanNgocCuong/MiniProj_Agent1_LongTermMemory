"""
Memory Domain Exceptions

Domain-specific exceptions.
"""


class MemoryDomainException(Exception):
    """Base exception for memory domain"""
    pass


class FactNotFoundError(MemoryDomainException):
    """Fact not found exception"""
    pass


class InvalidFactError(MemoryDomainException):
    """Invalid fact data exception"""
    pass


class ConversationNotFoundError(MemoryDomainException):
    """Conversation not found exception"""
    pass

