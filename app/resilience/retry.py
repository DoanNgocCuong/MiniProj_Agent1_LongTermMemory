"""
Retry logic with exponential backoff.
"""
import asyncio
import functools
from typing import Callable, TypeVar, Any
from app.core.logging import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    exceptions: tuple = (Exception,),
):
    """
    Decorator for retrying functions with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential backoff
        exceptions: Tuple of exceptions to catch and retry
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> T:
                delay = initial_delay
                last_exception = None
                
                for attempt in range(max_retries + 1):
                    try:
                        return await func(*args, **kwargs)
                    except exceptions as e:
                        last_exception = e
                        if attempt < max_retries:
                            logger.warning(
                                f"Attempt {attempt + 1}/{max_retries + 1} failed for {func.__name__}: {e}. "
                                f"Retrying in {delay:.2f}s..."
                            )
                            await asyncio.sleep(delay)
                            delay = min(delay * exponential_base, max_delay)
                        else:
                            logger.error(f"All {max_retries + 1} attempts failed for {func.__name__}")
                            raise
                
                # This should never be reached, but type checker needs it
                if last_exception:
                    raise last_exception
                raise RuntimeError("Unexpected retry logic error")
            
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> T:
                delay = initial_delay
                last_exception = None
                
                for attempt in range(max_retries + 1):
                    try:
                        return func(*args, **kwargs)
                    except exceptions as e:
                        last_exception = e
                        if attempt < max_retries:
                            logger.warning(
                                f"Attempt {attempt + 1}/{max_retries + 1} failed for {func.__name__}: {e}. "
                                f"Retrying in {delay:.2f}s..."
                            )
                            import time
                            time.sleep(delay)
                            delay = min(delay * exponential_base, max_delay)
                        else:
                            logger.error(f"All {max_retries + 1} attempts failed for {func.__name__}")
                            raise
                
                if last_exception:
                    raise last_exception
                raise RuntimeError("Unexpected retry logic error")
            
            return sync_wrapper
    
    return decorator

