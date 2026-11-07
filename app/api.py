"""HTTP API wrapper around the existing grounded RAG query path.

Transport only: this module does not change guards, retrieval, generation,
citation selection, or the Chroma store. The Streamlit UI remains available,
but Vercel hosts a separate Next.js frontend that calls these endpoints.
"""

from __future__ import annotations

import json
import logging
import os
import threading
from contextlib import asynccontextmanager
from dataclasses import asdict
from functools import lru_cache
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.ask import ask
from app.config import Config, load_config
from app.pipeline.onnx_embedder import get_onnx_embedder

logger = logging.getLogger("arth.api")

# Demo-sized concurrency: one answer at a time on the 0.1 vCPU free instance.
_ASK_SLOT = threading.BoundedSemaphore(1)
BUSY_MESSAGE = (
    "The assistant is answering another question right now. "
    "Please retry in a few seconds."
)


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


class Hit(BaseModel):
    chunk_id: str
    score: float
    distance: float
    text: str
    url: str
    title: str
    section: str
    page_id: str
    page_type: str
    scraped_at: str


class AskResponse(BaseModel):
    query_id: str
    decision: str
    answer: str
    citation_url: str | None = None
    last_updated: str | None = None
    educational_link: str | None = None
    hits: list[Hit] = Field(default_factory=list)


class SourceInfo(BaseModel):
    id: str
    type: str
    title: str
    url: str
    chunks: int


class MetaResponse(BaseModel):
    chunk_count: int
    source_count: int
    sources: list[SourceInfo]
    embedding_model: str
    embedding_dimension: int | None = None
    collection: str
    retrieval_k: int
    retrieval_min_score: float
    api_version: str = "1"


@lru_cache(maxsize=1)
def _config() -> Config:
    return load_config()


def _allowed_origins() -> list[str]:
    raw = os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000",
    )
    return [item.strip() for item in raw.split(",") if item.strip()]


def _ensure_index(config: Config) -> bool:
    """Rebuild the local Chroma store from committed artifacts if it is missing."""
    try:
        import chromadb
    except ImportError:
        return False
    try:
        client = chromadb.PersistentClient(path=str(config.chroma_dir))
        if config.collection in {item.name for item in client.list_collections()}:
            return True
        from app.pipeline.store import store_all

        _, failed = store_all(config)
        return not failed
    except Exception:
        return False


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    config = _config()
    # Fresh hosts have no chroma/ directory: build it from committed chunks + embeddings.
    _ensure_index(config)
    # Load the model once at startup so the first question does not time out.
    try:
        get_onnx_embedder(config.embedding_model)
    except Exception:
        logger.exception("ONNX embedder preload failed; /api/ask will retry lazily")
    yield


app = FastAPI(
    title="Arth AI — Grounded HDFC Mutual Fund API",
    version="1.0.0",
    description="HTTP wrapper around the existing guards → retrieve → generate path.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins(),
    # Preview deployments get a fresh *.vercel.app subdomain on every push.
    allow_origin_regex=os.getenv("ALLOWED_ORIGIN_REGEX", r"https://.*\.vercel\.app"),
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


def _chunk_counts(config: Config) -> tuple[dict[str, int], int]:
    try:
        index = json.loads(
            (config.chunks_dir / "_index.json").read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError):
        return {}, 0
    if not isinstance(index, dict):
        return {}, 0
    pages = index.get("pages") or []
    counts = {
        page["page_id"]: int(page.get("chunks") or 0)
        for page in pages
        if isinstance(page, dict) and page.get("page_id")
    }
    return counts, int(index.get("chunk_count") or 0)


def _embedding_dimension(config: Config) -> int | None:
    try:
        manifest = json.loads(
            (config.embeddings_dir / "manifest.json").read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(manifest, dict):
        return None
    dimension = int(manifest.get("dimension") or 0)
    return dimension or None


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/meta", response_model=MetaResponse)
def meta() -> MetaResponse:
    config = _config()
    counts, chunk_count = _chunk_counts(config)
    sources = [
        SourceInfo(
            id=source.id,
            type=source.type,
            title=source.title,
            url=source.url,
            chunks=counts.get(source.id, 0),
        )
        for source in config.sources
    ]
    return MetaResponse(
        chunk_count=chunk_count,
        source_count=len(sources),
        sources=sources,
        embedding_model=config.embedding_model,
        embedding_dimension=_embedding_dimension(config),
        collection=config.collection,
        retrieval_k=config.retrieval_k,
        retrieval_min_score=config.retrieval_min_score,
    )


@app.post("/api/ask", response_model=AskResponse)
def ask_endpoint(payload: AskRequest) -> AskResponse:
    question = payload.question.strip()
    if not question:
        raise HTTPException(status_code=422, detail="question must not be empty")

    if not _ASK_SLOT.acquire(blocking=False):
        raise HTTPException(status_code=503, detail=BUSY_MESSAGE)

    try:
        result = ask(question, config=_config())
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    finally:
        _ASK_SLOT.release()

    return AskResponse(
        query_id=result.query_id,
        decision=result.decision,
        answer=result.answer,
        citation_url=result.citation_url,
        last_updated=result.last_updated,
        educational_link=result.educational_link,
        hits=[Hit(**asdict(hit)) for hit in result.hits],
    )
