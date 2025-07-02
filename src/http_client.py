"""
HTTP client for the crypto crawler exercise.
"""

import aiohttp
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from .core.interfaces import IHttpClient


class HttpClient(IHttpClient):
    """HTTP client with retry, error handling, and rate limiting"""

    def __init__(
        self,
        timeout: int = 30,
        max_retries: int = 5,
        requests_per_second: float = 2.0
    ):
        self.timeout = timeout
        self.max_retries = max_retries
        self.requests_per_second = requests_per_second
        self.session: Optional[aiohttp.ClientSession] = None
        self.logger = logging.getLogger(__name__)

        self.last_request_time: Optional[datetime] = None
        self.min_interval = (
            1.0 / requests_per_second if requests_per_second > 0 else 0
        )

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            )
        return self.session

    async def _rate_limit(self) -> None:
        """Apply rate limiting"""
        if self.last_request_time is not None and self.min_interval > 0:
            elapsed = (datetime.now() - self.last_request_time).total_seconds()
            if elapsed < self.min_interval:
                sleep_time = self.min_interval - elapsed
                self.logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s")
                await asyncio.sleep(sleep_time)

        self.last_request_time = datetime.now()

    async def get(self, url: str, **kwargs) -> Dict[str, Any]:
        """Make GET request with rate limiting and exponential backoff retry"""
        await self._rate_limit()
        session = await self._get_session()

        for attempt in range(self.max_retries):
            try:
                self.logger.debug(
                    f"Making request to {url} (attempt {attempt + 1})"
                )

                async with session.get(url, **kwargs) as response:
                    if response.status >= 500:
                        if attempt < self.max_retries - 1:
                            delay = 2**attempt
                            self.logger.warning(
                                f"Server error {response.status}, "
                                f"retrying in {delay}s"
                            )
                            await asyncio.sleep(delay)
                            continue
                        else:
                            error_msg = (
                                f"Server error after {self.max_retries} "
                                f"attempts: {response.status}"
                            )
                            self.logger.error(error_msg)
                            raise aiohttp.ClientError(error_msg)

                    if response.status >= 400:
                        error_msg = (
                            f"Client error: {response.status} for {url}"
                        )
                        self.logger.error(error_msg)
                        raise aiohttp.ClientResponseError(
                            request_info=response.request_info,
                            history=response.history,
                            status=response.status,
                            message=error_msg,
                        )

                    data = await response.json()
                    self.logger.debug(f"Successfully fetched data from {url}")
                    return data

            except aiohttp.ClientResponseError:
                # Don't retry client errors (4xx)
                raise
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                if attempt < self.max_retries - 1:
                    delay = 2**attempt
                    self.logger.warning(
                        f"Request failed: {e}, retrying in {delay}s"
                    )
                    await asyncio.sleep(delay)
                    continue
                else:
                    self.logger.error(
                        f"Request failed after {self.max_retries} "
                        f"attempts: {e}"
                    )
                    raise e

        raise aiohttp.ClientError("Max retries exceeded")

    async def close(self) -> None:
        """Close the HTTP session"""
        if self.session and not self.session.closed:
            await self.session.close()
            self.logger.debug("HTTP session closed")

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
