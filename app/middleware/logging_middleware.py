"""
Logging middleware for request/response logging.
"""
import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.logging import get_logger, get_request_id, set_request_id
from uuid import uuid4

logger = get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for request/response logging with request ID."""
    
    async def dispatch(self, request: Request, call_next):
        """Process request and log details."""
        # Generate and set request ID
        request_id = str(uuid4())
        set_request_id(request_id)
        
        # Log request
        start_time = time.time()
        logger.info(
            f"Request: method={request.method}, "
            f"path={request.url.path}, request_id={request_id}"
        )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate latency
            latency_ms = (time.time() - start_time) * 1000
            
            # Log response
            logger.info(
                f"Response: status={response.status_code}, "
                f"latency_ms={latency_ms:.2f}, request_id={request_id}"
            )
            
            # Add request ID to response header
            response.headers["X-Request-ID"] = request_id
            
            return response
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            logger.error(
                f"Request error: error={str(e)}, "
                f"latency_ms={latency_ms:.2f}, request_id={request_id}"
            )
            raise

