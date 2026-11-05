from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import urlsplit

import httpx

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)
TIMEOUT_SECONDS = 30.0


@dataclass
class FetchResult:
    url: str
    status: int | None
    html: str
    error: str | None
    fetched_at: str
    final_url: str | None = None


def _url_key(value: str) -> tuple[str, str, str]:
    """Scheme/host/path key used to compare a redirect target with the source list."""
    parts = urlsplit(value)
    return (parts.scheme.lower(), parts.netloc.lower(), parts.path.rstrip("/"))


def fetch_url(url: str, allowed_urls: set[str]) -> FetchResult:
    """GET one configured URL. Never crawls hrefs or other hosts."""
    fetched_at = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    if url not in allowed_urls:
        return FetchResult(
            url=url,
            status=None,
            html="",
            error="blocked: URL is not in the configured source list",
            fetched_at=fetched_at,
        )

    allowed_keys = {_url_key(value) for value in allowed_urls}

    try:
        with httpx.Client(
            timeout=TIMEOUT_SECONDS,
            follow_redirects=True,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-IN,en;q=0.9",
            },
        ) as client:
            response = client.get(url)
    except httpx.HTTPError as exc:
        return FetchResult(
            url=url,
            status=None,
            html="",
            error=f"request_failed: {exc}",
            fetched_at=fetched_at,
        )

    final_url = str(response.url)
    html = response.text or ""
    error = None
    if _url_key(final_url) not in allowed_keys:
        error = f"blocked_redirect: {final_url} is not in the configured source list"
        html = ""
    elif response.status_code >= 400:
        error = f"http_{response.status_code}"
    elif not html.strip():
        error = "empty_body"

    return FetchResult(
        url=url,
        status=response.status_code,
        html=html,
        error=error,
        fetched_at=fetched_at,
        final_url=final_url,
    )
