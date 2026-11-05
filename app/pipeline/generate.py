"""Grounded generation: context-only Groq call, clamp length, cite from retrieval metadata."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime

from app.config import Config
from app.llm.groq import complete, get_llm_model
from app.pipeline.artifacts import write_json
from app.pipeline.retrieve import RetrievalHit, allowed_source_urls

NOT_INDEXED_FALLBACK = "The requested information is not in the indexed official pages."

SYSTEM_PROMPT = """You are a factual mutual fund FAQ assistant for a small set of indexed Groww pages.
Rules:
1. Answer using ONLY the facts in Context. Do not assume, calculate, extrapolate, or use outside knowledge.
2. If the question names a scheme or fact that is not clearly the same as a Context title/section, say it is not in the indexed official pages.
3. Keep the answer at most 3 sentences. Facts only. Never invent numbers, percentages, returns, or operational steps.
4. Do not give buy/sell advice or rank funds.
5. Output exactly two labeled lines:
ANSWER: <your <=3 sentence answer>
SOURCE_INDEX: <integer 1 to N of the context source used, or NONE>
"""


@dataclass(frozen=True)
class GenerationResult:
    query_id: str
    query: str
    answer: str
    citation_url: str | None
    citation_title: str | None
    scraped_at: str | None
    raw_response: str
    source_index: int | None
    is_fallback: bool
    last_updated_line: str | None
    trace_path: str


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _split_sentences(text: str) -> list[str]:
    chunks = re.split(r"(?<=[.!?])\s+", text.strip())
    return [chunk.strip() for chunk in chunks if chunk.strip()]


def _clamp_sentences(text: str, max_sentences: int = 3) -> str:
    sentences = _split_sentences(text)
    if len(sentences) <= max_sentences:
        return text.strip()
    return " ".join(sentences[:max_sentences]).strip()


def _strip_think(raw: str) -> str:
    return re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL | re.IGNORECASE).strip()


def _format_context(hits: list[RetrievalHit]) -> str:
    parts: list[str] = []
    for idx, hit in enumerate(hits, start=1):
        parts.append(
            f"[Source {idx}]\n"
            f"Title: {hit.title}\n"
            f"Section: {hit.section}\n"
            f"URL: {hit.url}\n"
            f"Content: {hit.text}\n"
        )
    return "\n".join(parts)


def _parse_completion(raw: str) -> tuple[str, int | None]:
    cleaned = _strip_think(raw)
    answer_match = re.search(
        r"ANSWER:\s*(.+?)(?=\n\s*SOURCE_INDEX:|\Z)",
        cleaned,
        re.DOTALL | re.IGNORECASE,
    )
    source_match = re.search(r"SOURCE_INDEX:\s*([0-9]+|NONE)", cleaned, re.IGNORECASE)

    if answer_match:
        answer = answer_match.group(1).strip()
    else:
        answer = cleaned.strip()

    source_idx: int | None = None
    if source_match:
        val = source_match.group(1).strip().upper()
        if val != "NONE" and val.isdigit():
            source_idx = int(val)

    return answer, source_idx


def _looks_unindexed(answer: str) -> bool:
    lowered = answer.lower()
    return (
        "not available in the indexed official pages" in lowered
        or "not in the indexed official pages" in lowered
        or "not in indexed official pages" in lowered
    )


def _strip_urls(text: str) -> str:
    """Remove URLs so citations can only come from retrieval metadata."""
    return re.sub(r"https?://\S+", "", text).strip()


def _numbers(text: str) -> list[float]:
    normalized = text.replace(",", "")
    return [float(token) for token in re.findall(r"\d+(?:\.\d+)?", normalized)]


def _has_ungrounded_number(answer: str, hits: list[RetrievalHit]) -> bool:
    """Reject answers that quote percentages/amounts absent from the retrieved context."""
    context = " ".join(f"{hit.title} {hit.text}" for hit in hits)
    context_numbers = set(_numbers(context))

    # Only enforce on numbers that look like a percentage, currency amount, or decimal.
    pattern = re.compile(
        r"(?:₹|rs\.?|inr)\s*\d[\d,]*(?:\.\d+)?|\d[\d,]*(?:\.\d+)?\s*%|\b\d+\.\d+\b",
        re.IGNORECASE,
    )
    for match in pattern.finditer(answer):
        values = _numbers(match.group(0))
        for value in values:
            if not any(abs(value - known) < 1e-9 for known in context_numbers):
                return True
    return False


def _select_hit(
    hits: list[RetrievalHit],
    source_idx: int | None,
    allowed: set[str],
) -> RetrievalHit | None:
    selected: RetrievalHit | None = None
    if source_idx is not None and 1 <= source_idx <= len(hits):
        selected = hits[source_idx - 1]
    elif hits:
        selected = hits[0]
    if selected is None or selected.url not in allowed:
        return next((hit for hit in hits if hit.url in allowed), None)
    return selected


def last_updated_line(scraped_at: str | None) -> str | None:
    if not scraped_at:
        return None
    return f"Last updated from sources: {scraped_at}"


def generate(
    query: str,
    hits: list[RetrievalHit],
    config: Config,
    query_id: str,
) -> GenerationResult:
    """Generate from retrieved hits only. Citation URL always comes from chunk metadata."""
    allowed = allowed_source_urls(config)
    trace_file = config.traces_dir / f"{query_id}_generation.json"

    if not hits:
        write_json(
            trace_file,
            {
                "query_id": query_id,
                "query": query,
                "timestamp": _now(),
                "answer": NOT_INDEXED_FALLBACK,
                "is_fallback": True,
                "fallback_reason": "no_hits",
                "citation": {"url": None, "title": None, "scraped_at": None},
            },
        )
        return GenerationResult(
            query_id=query_id,
            query=query,
            answer=NOT_INDEXED_FALLBACK,
            citation_url=None,
            citation_title=None,
            scraped_at=None,
            raw_response="",
            source_index=None,
            is_fallback=True,
            last_updated_line=None,
            trace_path=str(trace_file),
        )

    top_score = hits[0].score
    if top_score < config.retrieval_min_score:
        write_json(
            trace_file,
            {
                "query_id": query_id,
                "query": query,
                "timestamp": _now(),
                "answer": NOT_INDEXED_FALLBACK,
                "is_fallback": True,
                "fallback_reason": "low_relevance",
                "min_score": config.retrieval_min_score,
                "top_score": top_score,
                "hits": [
                    {"chunk_id": hit.chunk_id, "score": hit.score, "section": hit.section}
                    for hit in hits
                ],
                "citation": {"url": None, "title": None, "scraped_at": None},
            },
        )
        return GenerationResult(
            query_id=query_id,
            query=query,
            answer=NOT_INDEXED_FALLBACK,
            citation_url=None,
            citation_title=None,
            scraped_at=None,
            raw_response="",
            source_index=None,
            is_fallback=True,
            last_updated_line=None,
            trace_path=str(trace_file),
        )

    if config.llm_provider != "groq":
        raise RuntimeError(
            f"LLM provider {config.llm_provider!r} is not implemented. "
            "Set llm.provider to groq; do not switch providers silently."
        )

    context_str = _format_context(hits)
    user_prompt = f"Context:\n{context_str}\n\nQuestion: {query}\n\nAnswer according to the rules:"
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    raw_response = complete(messages, temperature=config.llm_temperature)
    parsed_answer, source_idx = _parse_completion(raw_response)
    parsed_answer = _strip_urls(parsed_answer)
    clamped_answer = _clamp_sentences(parsed_answer, max_sentences=3)

    fallback_reason: str | None = None
    if _looks_unindexed(clamped_answer):
        fallback_reason = "not_in_context"
    elif _has_ungrounded_number(clamped_answer, hits):
        fallback_reason = "ungrounded_number"
        clamped_answer = NOT_INDEXED_FALLBACK

    is_fallback = fallback_reason is not None
    selected = None if is_fallback else _select_hit(hits, source_idx, allowed)
    citation_url = selected.url if selected else None
    citation_title = selected.title if selected else None
    scraped_at = selected.scraped_at if selected else None

    payload = {
        "query_id": query_id,
        "query": query,
        "timestamp": _now(),
        "model": get_llm_model(),
        "provider": config.llm_provider,
        "temperature": config.llm_temperature,
        "raw_response": raw_response,
        "parsed_answer": parsed_answer,
        "final_answer": clamped_answer,
        "source_index": source_idx,
        "is_fallback": is_fallback,
        "fallback_reason": fallback_reason,
        "citation": {
            "url": citation_url,
            "title": citation_title,
            "scraped_at": scraped_at,
        },
    }
    write_json(trace_file, payload)

    return GenerationResult(
        query_id=query_id,
        query=query,
        answer=clamped_answer,
        citation_url=citation_url,
        citation_title=citation_title,
        scraped_at=scraped_at,
        raw_response=raw_response,
        source_index=source_idx,
        is_fallback=is_fallback,
        last_updated_line=last_updated_line(scraped_at),
        trace_path=str(trace_file),
    )
