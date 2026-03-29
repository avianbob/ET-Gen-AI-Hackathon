"""
HTTP client utilities with retry logic and rate limiting.
"""

import asyncio
import time
from typing import Optional, Dict, Any
from functools import wraps
import httpx
import aiohttp
from app.repurpose_settings import settings
from app.services.repurpose.utils.logger import get_logger

logger = get_logger("api_clients")


class RateLimiter:
    """Simple rate limiter using token bucket algorithm."""

    def __init__(self, rate: float):
        """
        Initialize rate limiter.

        Args:
            rate: Requests per second
        """
        self.rate = rate
        self.interval = 1.0 / rate if rate > 0 else 0
        self.last_request = 0.0

    async def acquire(self):
        """Wait if necessary to respect rate limit."""
        if self.interval > 0:
            now = time.time()
            time_since_last = now - self.last_request

            if time_since_last < self.interval:
                sleep_time = self.interval - time_since_last
                await asyncio.sleep(sleep_time)

            self.last_request = time.time()


def rate_limited(rate: float):
    """
    Decorator for rate-limited async functions.

    Args:
        rate: Requests per second
    """
    limiter = RateLimiter(rate)

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            await limiter.acquire()
            return await func(*args, **kwargs)
        return wrapper
    return decorator


async def retry_with_backoff(
    func,
    max_retries: int = 3,
    initial_delay: float = 2.0,
    backoff_factor: float = 2.0,
    *args,
    **kwargs
):
    """
    Retry a function with exponential backoff.

    Args:
        func: Async function to retry
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        backoff_factor: Multiplier for delay after each retry
        *args, **kwargs: Arguments to pass to func

    Returns:
        Result of func

    Raises:
        Exception from last retry attempt
    """
    delay = initial_delay
    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            last_exception = e

            if attempt < max_retries:
                logger.warning(
                    f"Attempt {attempt + 1}/{max_retries + 1} failed: {str(e)}. "
                    f"Retrying in {delay}s..."
                )
                await asyncio.sleep(delay)
                delay *= backoff_factor
            else:
                logger.error(f"All {max_retries + 1} attempts failed: {str(e)}")

    raise last_exception


class AsyncHTTPClient:
    """Async HTTP client with timeout and retry support."""

    def __init__(
        self,
        timeout: int = settings.API_TIMEOUT,
        max_retries: int = settings.MAX_RETRIES
    ):
        """
        Initialize HTTP client.

        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        """Async context manager entry."""
        self._client = httpx.AsyncClient(
            timeout=self.timeout,
            follow_redirects=True,
            headers={
                "User-Agent": "DrugRepurposingPlatform/1.0 (Research Tool; https://github.com/drug-repurposing)",
                "Accept": "application/json",
            }
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()

    async def get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        retry: bool = True
    ) -> Dict[str, Any]:
        """
        Perform GET request with retry logic.

        Args:
            url: Request URL
            params: Query parameters
            headers: Request headers (will override default headers)
            retry: Enable retry with exponential backoff

        Returns:
            JSON response as dictionary

        Raises:
            httpx.HTTPError: On request failure after retries
        """
        async def _make_request():
            if not self._client:
                raise RuntimeError("Client not initialized. Use async context manager.")

            # Merge default headers with custom headers (custom takes precedence)
            merged_headers = {
                "User-Agent": "DrugRepurposingPlatform/1.0 (Research Tool)",
                "Accept": "application/json",
            }
            if headers:
                merged_headers.update(headers)

            logger.debug(f"GET {url} with params: {params}")
            response = await self._client.get(url, params=params, headers=merged_headers)
            response.raise_for_status()
            return response.json()

        if retry:
            return await retry_with_backoff(
                _make_request,
                max_retries=self.max_retries,
                initial_delay=settings.RETRY_DELAY
            )
        else:
            return await _make_request()

    async def get_text(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        retry: bool = True
    ) -> str:
        """
        Perform GET request returning plain text (for APIs like KEGG that return text/plain).

        Args:
            url: Request URL
            params: Query parameters
            headers: Request headers
            retry: Enable retry with exponential backoff

        Returns:
            Response as plain text string

        Raises:
            httpx.HTTPError: On request failure after retries
        """
        async def _make_request():
            if not self._client:
                raise RuntimeError("Client not initialized. Use async context manager.")

            logger.debug(f"GET (text) {url} with params: {params}")
            response = await self._client.get(url, params=params, headers=headers)
            response.raise_for_status()
            return response.text

        if retry:
            return await retry_with_backoff(
                _make_request,
                max_retries=self.max_retries,
                initial_delay=settings.RETRY_DELAY
            )
        else:
            return await _make_request()

    async def post(
        self,
        url: str,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        retry: bool = True
    ) -> Dict[str, Any]:
        """
        Perform POST request with retry logic.

        Args:
            url: Request URL
            json: JSON request body
            data: Form data
            headers: Request headers
            retry: Enable retry with exponential backoff

        Returns:
            JSON response as dictionary

        Raises:
            httpx.HTTPError: On request failure after retries
        """
        async def _make_request():
            if not self._client:
                raise RuntimeError("Client not initialized. Use async context manager.")

            logger.debug(f"POST {url}")
            response = await self._client.post(
                url,
                json=json,
                data=data,
                headers=headers
            )
            response.raise_for_status()
            return response.json()

        if retry:
            return await retry_with_backoff(
                _make_request,
                max_retries=self.max_retries,
                initial_delay=settings.RETRY_DELAY
            )
        else:
            return await _make_request()


class AIOHTTPClient:
    """Alternative async HTTP client using aiohttp (for streaming, etc.)."""

    def __init__(self, timeout: int = settings.API_TIMEOUT):
        """
        Initialize aiohttp client.

        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self._session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Async context manager entry."""
        self._session = aiohttp.ClientSession(
            timeout=self.timeout,
            headers={
                "User-Agent": "DrugRepurposingPlatform/1.0 (Research Tool; https://github.com/drug-repurposing)",
                "Accept": "application/json",
            }
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._session:
            await self._session.close()

    async def get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Perform GET request.

        Args:
            url: Request URL
            params: Query parameters
            headers: Request headers

        Returns:
            JSON response as dictionary
        """
        if not self._session:
            raise RuntimeError("Session not initialized. Use async context manager.")

        async with self._session.get(url, params=params, headers=headers) as response:
            response.raise_for_status()
            return await response.json()

    async def post(
        self,
        url: str,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Perform POST request.

        Args:
            url: Request URL
            json: JSON request body
            data: Form data
            headers: Request headers

        Returns:
            JSON response as dictionary
        """
        if not self._session:
            raise RuntimeError("Session not initialized. Use async context manager.")

        async with self._session.post(
            url,
            json=json,
            data=data,
            headers=headers
        ) as response:
            response.raise_for_status()
            return await response.json()
