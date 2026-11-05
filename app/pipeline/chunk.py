"""Phase 4: turn loaded documents into metadata-aware chunks."""

from __future__ import annotations

import json
import re
from typing import Any

from app.config import Config, Source
from app.pipeline.artifacts import write_json, write_jsonl

DEFAULT_SIZE = 512
DEFAULT_OVERLAP = 64
DUPLICATE_SECTION_FACTS = {
    "investment objective": "investment-objective",
    "fund benchmark": "benchmark",
}


def _clean(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _slug(value: str) -> str:
    text = _clean(value).lower().replace("&", " and ")
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text or "section"


def _split_long_line(line: str, size: int) -> list[str]:
    """Split a single oversized line on sentence, clause, or word boundaries."""
    parts: list[str] = []
    remaining = line.strip()
    while len(remaining) > size:
        window = remaining[:size]
        break_at = max(
            window.rfind(". "),
            window.rfind("; "),
            window.rfind(", "),
            window.rfind(" "),
        )
        if break_at <= max(1, size // 3):
            break_at = window.rfind(" ")
        if break_at <= 0:
            break_at = size
        part = remaining[:break_at].strip()
        if part:
            parts.append(part)
        remaining = remaining[break_at:].strip()
    if remaining:
        parts.append(remaining)
    return parts


def _split_units(text: str, size: int) -> list[str]:
    """Break text into line-sized units without splitting words or fact lines."""
    units: list[str] = []
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        if len(line) <= size:
            units.append(line)
        else:
            units.extend(_split_long_line(line, size))
    return units


def _split_text(text: str, size: int, overlap: int) -> list[str]:
    """Pack whole lines into chunks, carrying at most `overlap` trailing lines."""
    text = _clean(text)
    if not text:
        return []
    if size <= 0 or len(text) <= size:
        return [text]

    overlap = max(0, min(overlap, size // 2))
    units = _split_units(text, size)
    parts: list[str] = []
    current: list[str] = []

    def joined_len(lines: list[str]) -> int:
        return sum(len(line) for line in lines) + max(0, len(lines) - 1)

    for unit in units:
        if current and joined_len(current + [unit]) > size:
            parts.append("\n".join(current))

            carried: list[str] = []
            for previous in reversed(current):
                candidate = [previous, *carried]
                if carried and joined_len(candidate) > overlap:
                    break
                carried = candidate
            if joined_len(carried + [unit]) > size:
                carried = []
            current = carried

        if not current and len(unit) > size:
            parts.extend(_split_long_line(unit, size))
            continue
        current.append(unit)

    if current:
        parts.append("\n".join(current))
    return parts


def _make_chunk(
    document: dict[str, Any],
    section: str,
    text: str,
    chunk_id: str,
) -> dict[str, Any]:
    return {
        "chunk_id": chunk_id,
        "page_id": document.get("page_id"),
        "url": document.get("url"),
        "title": document.get("title"),
        "section": section,
        "page_type": document.get("page_type"),
        "text": text,
        "char_count": len(text),
        "scraped_at": document.get("scraped_at"),
    }


def _fact_text(fact: dict[str, Any]) -> str:
    text = _clean(fact.get("text"))
    if text:
        return text
    label = _clean(fact.get("label"))
    value = _clean(fact.get("value"))
    if label and value:
        return f"{label}: {value}"
    return value


def _chunk_facts(document: dict[str, Any]) -> list[dict[str, Any]]:
    chunks: list[dict[str, Any]] = []
    seen: set[str] = set()
    page_id = _clean(document.get("page_id"))
    for fact in document.get("facts") or []:
        field = _clean(fact.get("field")) or _slug(fact.get("label") or "")
        text = _fact_text(fact)
        if not field or not text:
            continue
        chunk_id = f"{page_id}::{field}"
        if chunk_id in seen:
            continue
        seen.add(chunk_id)
        chunks.append(_make_chunk(document, field, text, chunk_id))
    return chunks


def _is_duplicate_section(heading: str, fact_fields: set[str]) -> bool:
    field = DUPLICATE_SECTION_FACTS.get(heading.strip().lower())
    return bool(field and field in fact_fields)


def _chunk_sections(
    document: dict[str, Any],
    fact_fields: set[str],
    size: int,
    overlap: int,
) -> list[dict[str, Any]]:
    chunks: list[dict[str, Any]] = []
    used_slugs: set[str] = set()
    page_id = _clean(document.get("page_id"))

    for section in document.get("sections") or []:
        heading = _clean(section.get("heading")) or "section"
        text = _clean(section.get("text"))
        if not text or _is_duplicate_section(heading, fact_fields):
            continue

        base_slug = _slug(heading)
        slug = base_slug
        suffix = 2
        while slug in used_slugs:
            slug = f"{base_slug}-{suffix}"
            suffix += 1
        used_slugs.add(slug)

        parts = _split_text(text, size, overlap)
        for index, part in enumerate(parts, start=1):
            chunk_id = (
                f"{page_id}::{slug}"
                if len(parts) == 1
                else f"{page_id}::{slug}::part-{index}"
            )
            chunks.append(_make_chunk(document, slug, part, chunk_id))
    return chunks


def _amc_key_information(document: dict[str, Any]) -> dict[str, str] | None:
    lines = [_fact_text(fact) for fact in document.get("facts") or []]
    lines = [line for line in lines if line]
    if not lines:
        return None
    return {"heading": "AMC key information", "text": "\n".join(lines)}


def chunk_document(document: dict[str, Any], config: Config) -> list[dict[str, Any]]:
    size = int(config.chunking.get("size", DEFAULT_SIZE))
    overlap = int(config.chunking.get("overlap", DEFAULT_OVERLAP))
    page_type = _clean(document.get("page_type"))

    if page_type == "amc":
        sections = list(document.get("sections") or [])
        key_information = _amc_key_information(document)
        if key_information:
            sections.insert(0, key_information)
        amc_document = {**document, "sections": sections}
        return _chunk_sections(amc_document, set(), size, overlap)

    facts = list(document.get("facts") or [])
    fact_fields = {_clean(fact.get("field")) for fact in facts}
    chunks = _chunk_facts(document)
    chunks.extend(_chunk_sections(document, fact_fields, size, overlap))
    return chunks


def chunk_source(config: Config, source: Source) -> tuple[list[dict[str, Any]], str | None]:
    loaded_path = config.loaded_dir / f"{source.id}.json"
    if not loaded_path.exists():
        return [], "missing loaded document"
    try:
        document = json.loads(loaded_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [], f"unreadable loaded document: {exc}"
    if not isinstance(document, dict):
        return [], "loaded document is not an object"

    chunks = chunk_document(document, config)
    if not chunks:
        return [], "no chunks produced"

    write_jsonl(config.chunks_dir / f"{source.id}.jsonl", chunks)
    return chunks, None


def chunk_all(config: Config) -> tuple[list[dict[str, Any]], bool]:
    results: list[dict[str, Any]] = []
    failed = False
    total_chunks = 0

    for source in config.sources:
        print(f"Chunking {source.id} [{source.type}]")
        chunks, error = chunk_source(config, source)
        if error:
            failed = True
            (config.chunks_dir / f"{source.id}.jsonl").unlink(missing_ok=True)
            print(f"  FAILED {error}")
            results.append(
                {
                    "page_id": source.id,
                    "page_type": source.type,
                    "ok": False,
                    "error": error,
                }
            )
            continue

        total_chunks += len(chunks)
        print(f"  ok chunks={len(chunks)}")
        results.append(
            {
                "page_id": source.id,
                "page_type": source.type,
                "ok": True,
                "chunks": len(chunks),
            }
        )

    write_json(
        config.chunks_dir / "_index.json",
        {
            "strategy": config.chunking.get("strategy", "section_fact"),
            "size": int(config.chunking.get("size", DEFAULT_SIZE)),
            "overlap": int(config.chunking.get("overlap", DEFAULT_OVERLAP)),
            "source_count": len(config.sources),
            "chunk_count": total_chunks,
            "failed": failed,
            "pages": results,
        },
    )
    return results, failed
