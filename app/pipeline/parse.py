from __future__ import annotations

import json
import re
from typing import Any

from bs4 import BeautifulSoup

SPARSE_CHAR_THRESHOLD = 500


def _visible_text(soup: BeautifulSoup) -> str:
    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()
    text = soup.get_text("\n")
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line)


def _script_json(soup: BeautifulSoup, script_id: str) -> Any | None:
    node = soup.find("script", id=script_id)
    if node is None or not node.string:
        return None
    try:
        return json.loads(node.string)
    except json.JSONDecodeError:
        return None


def _json_ld_blocks(soup: BeautifulSoup) -> list[Any]:
    blocks: list[Any] = []
    for node in soup.find_all("script", attrs={"type": "application/ld+json"}):
        raw = node.string or node.get_text() or ""
        raw = raw.strip()
        if not raw:
            continue
        try:
            blocks.append(json.loads(raw))
        except json.JSONDecodeError:
            continue
    return blocks


def extract_next_data(html: str) -> Any | None:
    """Return the page's __NEXT_DATA__ JSON, if present."""
    soup = BeautifulSoup(html, "lxml")
    return _script_json(soup, "__NEXT_DATA__")


def html_to_text(html: str) -> tuple[str, dict[str, Any]]:
    """Cleaned visible text plus in-page JSON counts. Does not fetch any links."""
    soup = BeautifulSoup(html, "lxml")
    next_data = _script_json(soup, "__NEXT_DATA__")
    json_ld = _json_ld_blocks(soup)
    visible = _visible_text(BeautifulSoup(html, "lxml")).strip()

    extras: dict[str, Any] = {
        "has_next_data": next_data is not None,
        "json_ld_count": len(json_ld),
        "sparse": len(visible) < SPARSE_CHAR_THRESHOLD,
        "char_count_visible": len(visible),
        "char_count_text": len(visible),
    }
    return visible, extras
