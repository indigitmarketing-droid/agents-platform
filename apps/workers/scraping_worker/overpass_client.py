"""HTTP client for Overpass API with retries, backoff, and mirror fallback."""
import asyncio
import logging
import httpx

logger = logging.getLogger(__name__)


class OverpassError(Exception):
    pass


class OverpassRateLimitError(OverpassError):
    pass


class OverpassUnreachableError(OverpassError):
    pass


class OverpassClient:
    PRIMARY = "https://overpass-api.de/api/interpreter"
    MIRRORS = [
        "https://overpass.kumi.systems/api/interpreter",
        "https://overpass.private.coffee/api/interpreter",
    ]

    def __init__(
        self,
        max_concurrent: int = 2,
        initial_backoff: float = 5.0,
        timeout_seconds: float = 90.0,
    ):
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._initial_backoff = initial_backoff
        self._timeout = timeout_seconds
        self._endpoints = [self.PRIMARY] + self.MIRRORS

    async def query(self, ql_query: str, max_retries: int = 3) -> list[dict]:
        async with self._semaphore:
            last_error: Exception | None = None
            for endpoint in self._endpoints:
                try:
                    return await self._try_endpoint(endpoint, ql_query, max_retries)
                except OverpassRateLimitError as e:
                    logger.warning(f"Rate limited on {endpoint}, trying next mirror")
                    last_error = e
                except (httpx.HTTPError, OverpassError) as e:
                    logger.warning(f"Endpoint {endpoint} failed: {e}, trying next")
                    last_error = e
            if isinstance(last_error, OverpassRateLimitError):
                raise last_error
            raise OverpassUnreachableError(f"All endpoints failed. Last error: {last_error}")

    async def _try_endpoint(
        self, endpoint: str, ql_query: str, max_retries: int
    ) -> list[dict]:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            for attempt in range(max_retries):
                response = await client.post(endpoint, data={"data": ql_query})
                if response.status_code == 200:
                    payload = response.json()
                    return payload.get("elements", [])
                if response.status_code == 429:
                    wait = self._initial_backoff * (3 ** attempt)
                    logger.info(f"Rate limited, waiting {wait}s before retry")
                    await asyncio.sleep(wait)
                    continue
                if 500 <= response.status_code < 600:
                    raise OverpassError(f"Server error {response.status_code}")
                response.raise_for_status()
            raise OverpassRateLimitError(f"Max retries exceeded on {endpoint}")
