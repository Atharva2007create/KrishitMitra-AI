import hashlib
from dataclasses import dataclass
from urllib.parse import urldefrag, urlparse

import httpx

APPROVED_HOSTS = {"icar.gov.in", "www.icar.gov.in", "icar-iipr.org.in", "www.icar-iipr.org.in"}
ALLOWED_MIME_TYPES = {"application/pdf", "text/html", "application/xhtml+xml"}


class AcquisitionError(RuntimeError):
    pass


@dataclass(frozen=True)
class AcquiredDocument:
    canonical_url: str
    content: bytes
    mime_type: str
    checksum: str


def canonicalize_url(url: str) -> str:
    clean, _ = urldefrag(url.strip())
    parsed = urlparse(clean)
    if parsed.scheme != "https" or parsed.hostname not in APPROVED_HOSTS:
        raise AcquisitionError("Source URL is not an approved official HTTPS host")
    return parsed._replace(query="").geturl().rstrip("/")


async def acquire(url: str, timeout_seconds: float = 45) -> AcquiredDocument:
    canonical = canonicalize_url(url)
    headers = {"User-Agent": "KrishiMitraAI/1.0 official-document-ingestion"}
    async with httpx.AsyncClient(
        follow_redirects=True, timeout=timeout_seconds, headers=headers
    ) as client:
        response = await client.get(canonical)
        response.raise_for_status()
    final_url = canonicalize_url(str(response.url))
    content_type = response.headers.get("content-type", "").split(";", 1)[0].lower()
    if content_type not in ALLOWED_MIME_TYPES:
        raise AcquisitionError(
            f"Unsupported official document MIME type: {content_type or 'unknown'}"
        )
    if not response.content:
        raise AcquisitionError("Official source returned an empty document")
    return AcquiredDocument(
        canonical_url=final_url,
        content=response.content,
        mime_type=content_type,
        checksum=hashlib.sha256(response.content).hexdigest(),
    )
