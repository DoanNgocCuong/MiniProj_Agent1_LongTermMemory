"""
Application-wide Constants and Enums
"""

from enum import Enum


class FactCategory(str, Enum):
    """Fact categories extracted from conversations"""
    PREFERENCE = "preference"
    EXPERIENCE = "experience"
    HABIT = "habit"
    EMOTION = "emotion"
    RELATIONSHIP = "relationship"
    LEARNING = "learning"
    UNKNOWN = "unknown"


class JobStatus(str, Enum):
    """Job status for async operations"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# API Constants
MAX_PAGE_SIZE = 100
DEFAULT_PAGE_SIZE = 20

MAX_CONVERSATION_LENGTH = 100
MAX_MESSAGE_LENGTH = 5000
MAX_QUERY_LENGTH = 500

# Cache TTLs (in seconds)
CACHE_TTL_SEARCH_RESULTS = 300  # 5 minutes
CACHE_TTL_USER_FACTS = 600  # 10 minutes
CACHE_TTL_RATE_LIMIT = 60  # 1 minute

# Similarity Thresholds
DEFAULT_SIMILARITY_THRESHOLD = 0.4
MIN_SIMILARITY_THRESHOLD = 0.3
MAX_SIMILARITY_THRESHOLD = 0.9

# Rate Limiting
DEFAULT_RATE_LIMIT = 1000  # requests per minute
BURST_RATE_LIMIT = 100  # requests per second

