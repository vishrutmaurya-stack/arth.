"""Query path: PII/intent guards → retrieve → generate → cite from chunk metadata."""

from __future__ import annotations

import argparse
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime

from app.config import Config, ensure_dirs, load_config
from app.pipeline.artifacts import write_json
from app.pipeline.generate import GenerationResult, generate, last_updated_line
from app.pipeline.guards import GuardResult, evaluate_guards
from app.pipeline.retrieve import EmptyIndexError, RetrievalHit, RetrievalResult, retrieve

INGEST_MESSAGE = "The index is empty. Run ingest first (`python -m app.ingest --from-phase scrape`)."
PII_TRACE_NOTE = "raw query omitted because PII was detected"


@dataclass(frozen=True)
class AskResult:
    query_id: str
    decision: str
    answer: str
    citation_url: str | None
    last_updated: str | None
    educational_link: str | None
    hits: list[RetrievalHit]
    retrieval: RetrievalResult | None
    generation: GenerationResult | None
    display: str


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _compose_display(
    answer: str,
    citation_url: str | None,
    last_updated: str | None,
    educational_link: str | None,
) -> str:
    lines = [answer.strip()]
    link = citation_url or educational_link
    if link:
        lines.append("")
        lines.append(link)
    updated = last_updated_line(last_updated) if last_updated and not last_updated.startswith("Last updated") else last_updated
    if updated:
        lines.append("")
        lines.append(updated)
    return "\n".join(lines).strip()


def _write_guard_trace(
    config: Config,
    query_id: str,
    decision: str,
    *,
    query: str | None,
    message: str,
    educational_link: str | None,
) -> str:
    path = config.traces_dir / f"{query_id}_guard.json"
    payload: dict[str, object] = {
        "query_id": query_id,
        "decision": decision,
        "timestamp": _now(),
        "message": message,
        "educational_link": educational_link,
        "retrieved": False,
    }
    if query is None:
        payload["query"] = PII_TRACE_NOTE
        payload["pii_blocked"] = True
    else:
        payload["query"] = query
    write_json(path, payload)
    return str(path)


def _from_guard(query_id: str, guard: GuardResult) -> AskResult:
    display = _compose_display(
        guard.message or "",
        citation_url=None,
        last_updated=None,
        educational_link=guard.educational_link,
    )
    return AskResult(
        query_id=query_id,
        decision=guard.decision,
        answer=guard.message or "",
        citation_url=None,
        last_updated=None,
        educational_link=guard.educational_link,
        hits=[],
        retrieval=None,
        generation=None,
        display=display,
    )


def ask(query: str, config: Config | None = None) -> AskResult:
    """Run the step-7 query path. Guards run before retrieve; PII is never written to traces."""
    if config is None:
        config = load_config()
    ensure_dirs(config)
    query_id = uuid.uuid4().hex[:12]
    cleaned = (query or "").strip()
    if not cleaned:
        empty = GuardResult(
            allowed=False,
            decision="refuse_empty",
            message="Please enter a question about the indexed HDFC scheme pages.",
        )
        _write_guard_trace(
            config,
            query_id,
            empty.decision,
            query=cleaned,
            message=empty.message or "",
            educational_link=None,
        )
        return _from_guard(query_id, empty)

    guard = evaluate_guards(cleaned, config)
    if not guard.allowed:
        _write_guard_trace(
            config,
            query_id,
            guard.decision,
            query=None if guard.decision == "refuse_pii" else cleaned,
            message=guard.message or "",
            educational_link=guard.educational_link,
        )
        return _from_guard(query_id, guard)

    try:
        retrieval = retrieve(cleaned, config, query_id=query_id)
    except EmptyIndexError:
        message = INGEST_MESSAGE
        _write_guard_trace(
            config,
            query_id,
            "empty_index",
            query=cleaned,
            message=message,
            educational_link=None,
        )
        return AskResult(
            query_id=query_id,
            decision="empty_index",
            answer=message,
            citation_url=None,
            last_updated=None,
            educational_link=None,
            hits=[],
            retrieval=None,
            generation=None,
            display=message,
        )

    generation = generate(cleaned, retrieval.hits, config, query_id=query_id)
    display = _compose_display(
        generation.answer,
        citation_url=generation.citation_url,
        last_updated=generation.scraped_at,
        educational_link=None,
    )
    return AskResult(
        query_id=query_id,
        decision="answer" if not generation.is_fallback else "not_in_corpus",
        answer=generation.answer,
        citation_url=generation.citation_url,
        last_updated=generation.scraped_at,
        educational_link=None,
        hits=retrieval.hits,
        retrieval=retrieval,
        generation=generation,
        display=display,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Ask a factual question against the Groww HDFC index.")
    parser.add_argument("question", nargs="+", help="User question")
    args = parser.parse_args()
    question = " ".join(args.question)
    try:
        result = ask(question)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
    print(result.display)
    if result.retrieval:
        print(f"\n[trace] {result.retrieval.trace_path}")
    if result.generation:
        print(f"[trace] {result.generation.trace_path}")


if __name__ == "__main__":
    main()
