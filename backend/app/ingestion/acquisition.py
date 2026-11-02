import hashlib
from dataclasses import dataclass
from urllib.parse import urldefrag, urljoin, urlparse

import httpx

APPROVED_HOSTS = {"icar.gov.in", "www.icar.gov.in", "icar-iipr.org.in", "www.icar-iipr.org.in"}
ALLOWED_MIME_TYPES = {"application/pdf", "text/html", "application/xhtml+xml"}
MAX_DOCUMENT_BYTES = 20 * 1024 * 1024
MAX_REDIRECTS = 5


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


async def acquire(
    url: str,
    timeout_seconds: float = 45,
    max_bytes: int = MAX_DOCUMENT_BYTES,
    transport: httpx.AsyncBaseTransport | None = None,
) -> AcquiredDocument:
    canonical = canonicalize_url(url)
    headers = {"User-Agent": "KrishiMitraAI/1.0 official-document-ingestion"}
    async with httpx.AsyncClient(
        follow_redirects=False,
        timeout=timeout_seconds,
        headers=headers,
        transport=transport,
    ) as client:
        current = canonical
        for _ in range(MAX_REDIRECTS + 1):
            async with client.stream("GET", current) as response:
                if response.is_redirect:
                    location = response.headers.get("location")
                    if not location:
                        raise AcquisitionError("Official source returned an invalid redirect")
                    current = canonicalize_url(urljoin(current, location))
                    continue
                response.raise_for_status()
                content_type = response.headers.get("content-type", "").split(";", 1)[0].lower()
                if content_type not in ALLOWED_MIME_TYPES:
                    raise AcquisitionError(
                        f"Unsupported official document MIME type: {content_type or 'unknown'}"
                    )
                declared_size = response.headers.get("content-length")
                if declared_size:
                    try:
                        if int(declared_size) > max_bytes:
                            raise AcquisitionError(
                                "Official document exceeds the configured size limit"
                            )
                    except ValueError as exc:
                        raise AcquisitionError(
                            "Official source returned an invalid content length"
                        ) from exc
                chunks: list[bytes] = []
                received = 0
                async for chunk in response.aiter_bytes():
                    received += len(chunk)
                    if received > max_bytes:
                        raise AcquisitionError(
                            "Official document exceeds the configured size limit"
                        )
                    chunks.append(chunk)
                content = b"".join(chunks)
                final_url = canonicalize_url(str(response.url))
                break
        else:
            raise AcquisitionError("Official source exceeded the redirect limit")
    if not content:
        raise AcquisitionError("Official source returned an empty document")
    return AcquiredDocument(
        canonical_url=final_url,
        content=content,
        mime_type=content_type,
        checksum=hashlib.sha256(content).hexdigest(),
    )
