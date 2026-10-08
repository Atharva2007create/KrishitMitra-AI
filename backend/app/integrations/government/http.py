import asyncio
from collections.abc import Mapping
from typing import Any
from urllib.parse import urlparse

import httpx


class GovernmentSourceError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class SafeGovernmentHttpClient:
    """Bounded HTTPS client for explicit official hosts; redirects are intentionally disabled."""

    def __init__(
        self,
        allowed_hosts: set[str],
        timeout_seconds: float,
        max_retries: int,
        max_response_bytes: int,
    ) -> None:
        self.allowed_hosts = {item.lower() for item in allowed_hosts}
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.max_response_bytes = max_response_bytes

    def _validate_url(self, url: str) -> None:
        parsed = urlparse(url)
        if parsed.scheme != "https" or parsed.hostname is None:
            raise GovernmentSourceError("UNSAFE_SOURCE_URL", "Official sources must use HTTPS")
        if parsed.hostname.lower() not in self.allowed_hosts:
            raise GovernmentSourceError("UNAPPROVED_SOURCE_HOST", "Source host is not approved")
        if parsed.username or parsed.password or parsed.port not in (None, 443):
            raise GovernmentSourceError("UNSAFE_SOURCE_URL", "Source URL authority is invalid")

    async def get_json(
        self,
        url: str,
        *,
        params: Mapping[str, str] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> Any:
        self._validate_url(url)
        for attempt in range(self.max_retries + 1):
            try:
                async with httpx.AsyncClient(
                    timeout=self.timeout_seconds,
                    follow_redirects=False,
                    headers={"Accept": "application/json", "User-Agent": "KrishiMitra-AI/1.0"},
                ) as client:
                    response = await client.get(url, params=params, headers=headers)
                if 300 <= response.status_code < 400:
                    raise GovernmentSourceError(
                        "SOURCE_REDIRECT_REJECTED", "Official source returned a redirect"
                    )
                if response.status_code in (401, 403):
                    raise GovernmentSourceError(
                        "SOURCE_AUTHENTICATION_REQUIRED", "Official source requires credentials"
                    )
                response.raise_for_status()
                length = response.headers.get("content-length")
                if length and int(length) > self.max_response_bytes:
                    raise GovernmentSourceError(
                        "SOURCE_RESPONSE_TOO_LARGE", "Response is too large"
                    )
                if len(response.content) > self.max_response_bytes:
                    raise GovernmentSourceError(
                        "SOURCE_RESPONSE_TOO_LARGE", "Response is too large"
                    )
                content_type = response.headers.get("content-type", "").lower()
                if "json" not in content_type:
                    raise GovernmentSourceError(
                        "SOURCE_CONTENT_TYPE_INVALID", "Official source did not return JSON"
                    )
                return response.json()
            except GovernmentSourceError:
                raise
            except (httpx.HTTPError, ValueError) as exc:
                if attempt >= self.max_retries:
                    raise GovernmentSourceError(
                        "LIVE_DATA_UNAVAILABLE", "Official source is temporarily unavailable"
                    ) from exc
                await asyncio.sleep(0.25 * (2**attempt))
        raise GovernmentSourceError("LIVE_DATA_UNAVAILABLE", "Official source unavailable")
