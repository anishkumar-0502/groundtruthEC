"""Portal HTTP client with process-wide asynchronous rate limiter."""

import asyncio
import logging
import time
from typing import Any, Dict, Optional, Tuple
import httpx

from app.config import settings
from app.errors import PortalError

logger = logging.getLogger("ground_truth.portal_client")


class PortalRateLimiter:
    """Process-wide asynchronous rate limiter ensuring serialized requests and minimum spacing."""

    def __init__(self, min_interval_seconds: float = 2.0):
        self.min_interval = min_interval_seconds
        self._lock = asyncio.Lock()
        self._last_request_start: float = 0.0

    async def acquire(self) -> None:
        """Wait until at least min_interval has passed since the last request start.

        Serializes all outbound calls to prevent concurrent execution.
        """
        await self._lock.acquire()
        try:
            now = time.monotonic()
            elapsed = now - self._last_request_start
            wait_time = self.min_interval - elapsed
            if wait_time > 0:
                logger.debug(f"Rate limiter pacing: sleeping for {wait_time:.3f}s")
                await asyncio.sleep(wait_time)
            self._last_request_start = time.monotonic()
        finally:
            self._lock.release()


# Process-wide shared rate limiter singleton
portal_rate_limiter = PortalRateLimiter(min_interval_seconds=settings.portal_rate_limit_seconds)


class PortalHttpClient:
    """HTTP client wrapper for TNREGINET portal operations.

    Enforces rate limiting, timeout handling, cookie isolation, and clean error reporting.
    """

    def __init__(self, cookies: Optional[httpx.Cookies] = None, timeout: Optional[float] = None):
        self.base_url = settings.portal_base_url
        self.timeout = timeout or settings.portal_timeout_seconds
        self.headers = {
            "User-Agent": settings.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=self.headers,
            cookies=cookies,
            follow_redirects=True,
            timeout=self.timeout,
        )

    @property
    def cookies(self) -> httpx.Cookies:
        return self._client.cookies

    async def request(
        self,
        method: str,
        path_or_url: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> httpx.Response:
        """Execute rate-limited request with sanitized logging and robust error handling."""
        # Enforce process-wide rate limiter
        await portal_rate_limiter.acquire()

        req_headers = dict(headers or {})

        # Normalize URL to prevent duplicate /portal/portal/ path prefix
        normalized_path = path_or_url
        if self.base_url.rstrip("/").endswith("/portal") and normalized_path.startswith("/portal/"):
            normalized_path = normalized_path[len("/portal"):]

        # Log sanitized request info
        safe_params = {k: ("***" if "captcha" in k.lower() else v) for k, v in (params or {}).items()}
        logger.info(f"Portal request: {method.upper()} {normalized_path} params={safe_params}")

        try:
            response = await self._client.request(
                method=method,
                url=normalized_path,
                params=params,
                data=data,
                headers=req_headers,
            )
        except httpx.TimeoutException as exc:
            logger.error(f"Portal timeout connecting to {normalized_path}: {exc}")
            raise PortalError(f"Portal request timed out after {self.timeout}s") from exc
        except httpx.NetworkError as exc:
            logger.error(f"Portal network error connecting to {normalized_path}: {exc}")
            raise PortalError("Failed to reach TNREGINET portal network") from exc
        except Exception as exc:
            logger.error(f"Unexpected error executing portal request to {normalized_path}: {exc}")
            raise PortalError(f"Unexpected portal communication error: {str(exc)}") from exc

        # Check HTTP status codes
        if response.status_code >= 500:
            logger.warning(f"Portal returned server error status {response.status_code}")
            raise PortalError(f"Portal server returned HTTP {response.status_code}")

        return response

    async def get(
        self,
        path_or_url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> httpx.Response:
        return await self.request("GET", path_or_url, params=params, headers=headers)

    async def post(
        self,
        path_or_url: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> httpx.Response:
        return await self.request("POST", path_or_url, params=params, data=data, headers=headers)

    async def close(self) -> None:
        """Close underlying HTTP client."""
        await self._client.aclose()

