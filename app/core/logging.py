"""
Structured Logging Setup

Configures structured JSON logging for production environments.
"""

import logging
import sys
from typing import Optional

from app.core.config import settings


def setup_logging(log_level: Optional[str] = None) -> logging.Logger:
    """
    Setup structured logging
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        
    Returns:
        Configured logger instance
    """
    level = log_level or settings.LOG_LEVEL
    log_format = settings.LOG_FORMAT
    
    # Create logger
    logger = logging.getLogger("pika_memory")
    logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, level.upper()))
    
    # Set formatter
    if log_format == "json":
        try:
            import structlog
            # Use structlog for JSON formatting
            processor = structlog.processors.JSONRenderer()
            handler.setFormatter(logging.Formatter("%(message)s"))
        except ImportError:
            # Fallback to standard formatter if structlog not available
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
            handler.setFormatter(formatter)
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    return logger


# Global logger instance
logger = setup_logging()

