# src/mueta/engine/retry.py
"""Retry utilities with exponential backoff."""

import time
import functools
from typing import TypeVar, Callable, Any
from loguru import logger
import httpx
from mueta.utils.errors import translate_http_error

T = TypeVar("T")


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    exceptions: tuple = (httpx.HTTPStatusError, httpx.ConnectError, httpx.TimeoutException),
) -> Callable:
    """
    Decorator for retrying functions with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts.
        base_delay: Initial delay in seconds.
        max_delay: Maximum delay cap in seconds.
        exceptions: Tuple of exceptions to catch and retry.

    Returns:
        Decorated function with retry logic.
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt < max_retries:
                        # Calculate delay with exponential backoff
                        delay = min(base_delay * (2 ** attempt), max_delay)
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_retries + 1} failed: {e}. "
                            f"Retrying in {delay:.1f}s..."
                        )
                        time.sleep(delay)
                    else:
                        logger.error(f"All {max_retries + 1} attempts failed: {e}")

            raise last_exception

        return wrapper
    return decorator


def make_request_with_retry(
    client: httpx.Client,
    method: str,
    url: str,
    max_retries: int = 3,
    **kwargs: Any,
) -> httpx.Response:
    """
    Make HTTP request with automatic retry on failure.

    Args:
        client: httpx.Client instance.
        method: HTTP method ('get', 'post', etc.).
        url: Request URL.
        max_retries: Maximum retry attempts.
        **kwargs: Additional arguments for the request.

    Returns:
        httpx.Response object.
    """
    last_exception = None
    base_delay = 1.0

    for attempt in range(max_retries + 1):
        try:
            if method.lower() == 'get':
                response = client.get(url, **kwargs)
            elif method.lower() == 'post':
                response = client.post(url, **kwargs)
            else:
                response = client.request(method, url, **kwargs)

            response.raise_for_status()
            return response

        except (httpx.HTTPStatusError, httpx.ConnectError, httpx.TimeoutException) as e:
            last_exception = e

            # Check if it's a retryable status code (5xx, 429)
            if isinstance(e, httpx.HTTPStatusError):
                if e.response.status_code < 500 and e.response.status_code != 429:
                    raise  # Don't retry client errors (4xx except 429)

            if attempt < max_retries:
                delay = min(base_delay * (2 ** attempt), 30.0)
                friendly_error = translate_http_error(e)
                logger.warning(
                    f"Request failed (attempt {attempt + 1}/{max_retries + 1}): {friendly_error}. "
                    f"Retrying in {delay:.1f}s..."
                )
                time.sleep(delay)
            else:
                friendly_error = translate_http_error(e)
                logger.error(f"Request failed after {max_retries + 1} attempts: {friendly_error}")

    raise last_exception
