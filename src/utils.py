"""
Utility functions and decorators for the scraping project.
"""

import functools
import asyncio
from typing import Callable, Any, Optional
from . import config


def retry_on_error(
    max_attempts: Optional[int] = None,
    delay: Optional[float] = None,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """
    Decorator that retries an async function on failure with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts (None = use config)
        delay: Initial delay between retries in seconds (None = use config)
        backoff: Multiplier for delay after each attempt (default: 2.0)
        exceptions: Tuple of exceptions to catch (default: all Exception)
    
    Returns:
        Decorated function that will retry on failure
    
    Example:
        @retry_on_error(max_attempts=3, delay=2.0)
        async def fetch_page(url):
            return await page.goto(url)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # Get retry settings from config if not provided
            attempts = max_attempts if max_attempts is not None else config.get_retry_count()
            retry_delay = delay if delay is not None else config.get_retry_delay()
            
            # If retry count is 0, just call the function once
            if attempts == 0:
                return await func(*args, **kwargs)
            
            last_exception = None
            
            for attempt in range(attempts):
                try:
                    result = await func(*args, **kwargs)
                    # Log success on retry
                    if attempt > 0:
                        # Get logger from first arg if available (self.log)
                        if args and hasattr(args[0], 'log'):
                            args[0].log.debug(f"Retry successful after {attempt} attempt(s)", 
                                            function=func.__name__)
                    return result
                    
                except exceptions as e:
                    last_exception = e
                    
                    # On last attempt, re-raise the exception
                    if attempt == attempts - 1:
                        raise
                    
                    # Calculate wait time with exponential backoff
                    wait_time = retry_delay * (backoff ** attempt)
                    
                    # Log retry attempt
                    if args and hasattr(args[0], 'log'):
                        args[0].log.debug(
                            f"Retry attempt {attempt + 1}/{attempts} after error",
                            function=func.__name__,
                            error=str(e),
                            wait_time=f"{wait_time:.1f}s"
                        )
                    
                    # Wait before retrying
                    await asyncio.sleep(wait_time)
            
            # Should never reach here, but just in case
            if last_exception:
                raise last_exception
                
        return wrapper
    return decorator


def retry_on_timeout(max_attempts: Optional[int] = None, delay: Optional[float] = None):
    """
    Specialized retry decorator for timeout errors.
    
    Args:
        max_attempts: Maximum number of retry attempts (None = use config)
        delay: Initial delay between retries in seconds (None = use config)
    
    Returns:
        Decorated function that will retry on timeout
    
    Example:
        @retry_on_timeout(max_attempts=3)
        async def load_page(url):
            return await page.goto(url, timeout=90000)
    """
    from playwright.async_api import TimeoutError as PlaywrightTimeout
    
    return retry_on_error(
        max_attempts=max_attempts,
        delay=delay,
        backoff=1.5,  # Gentler backoff for timeouts
        exceptions=(PlaywrightTimeout, TimeoutError, asyncio.TimeoutError)
    )


def retry_on_network_error(max_attempts: Optional[int] = None, delay: Optional[float] = None):
    """
    Specialized retry decorator for network errors.
    
    Args:
        max_attempts: Maximum number of retry attempts (None = use config)
        delay: Initial delay between retries in seconds (None = use config)
    
    Returns:
        Decorated function that will retry on network errors
    
    Example:
        @retry_on_network_error(max_attempts=5)
        async def fetch_data(url):
            return await session.get(url)
    """
    from playwright.async_api import Error as PlaywrightError
    
    return retry_on_error(
        max_attempts=max_attempts,
        delay=delay,
        backoff=2.0,
        exceptions=(PlaywrightError, ConnectionError, OSError)
    )


async def sleep_with_jitter(duration: float, jitter: float = 0.1):
    """
    Sleep for a duration with added random jitter to avoid thundering herd.
    
    Args:
        duration: Base sleep duration in seconds
        jitter: Maximum jitter to add as fraction of duration (default: 0.1 = 10%)
    
    Example:
        await sleep_with_jitter(1.0, jitter=0.2)  # Sleep 0.8-1.2 seconds
    """
    import random
    jitter_amount = duration * jitter
    actual_duration = duration + random.uniform(-jitter_amount, jitter_amount)
    await asyncio.sleep(max(0, actual_duration))

