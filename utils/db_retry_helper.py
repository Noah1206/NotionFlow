"""
Database Retry Helper
Provides retry logic for database operations that might fail due to resource issues
"""

import time
import functools
from typing import Any, Callable, Optional

def retry_db_operation(max_retries: int = 3, delay: float = 0.1, backoff: float = 2.0):
    """
    Decorator to retry database operations that might fail due to resource unavailability

    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries (seconds)
        backoff: Multiplier for delay after each retry
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            current_delay = delay

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    error_str = str(e).lower()

                    # Check if this is a resource temporarily unavailable error
                    if ('errno 11' in error_str or
                        'resource temporarily unavailable' in error_str or
                        'connection timeout' in error_str or
                        'database is locked' in error_str):

                        if attempt < max_retries:
                            print(f"⚠️ Database operation failed (attempt {attempt + 1}/{max_retries + 1}): {e}")
                            print(f"🔄 Retrying in {current_delay:.2f} seconds...")
                            time.sleep(current_delay)
                            current_delay *= backoff
                            continue

                    # If it's not a retry-able error or we've exhausted retries, raise immediately
                    raise e

            # If we get here, we've exhausted all retries
            print(f"❌ Database operation failed after {max_retries + 1} attempts")
            raise last_exception

        return wrapper
    return decorator

def safe_db_call(func: Callable, *args, **kwargs) -> Optional[Any]:
    """
    Safe wrapper for database calls with automatic retry
    Returns None if operation fails after all retries
    """
    try:
        @retry_db_operation(max_retries=3, delay=0.1)
        def wrapped_call():
            return func(*args, **kwargs)

        return wrapped_call()
    except Exception as e:
        print(f"❌ Database operation failed permanently: {e}")
        return None