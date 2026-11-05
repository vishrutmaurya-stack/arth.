"""Phase 7 retrieval: embed the question with MiniLM, query Chroma, write a trace."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.config import Config
from app.pipeline.artifacts import write_json

_EMBEDDER = None
_EMBEDDER_NAME: str | None = None
_CHROMA_COLLECTION = None
_CHROMA_PATH: str | None = None
_CHROMA_NAME: str | None = None


class EmptyIndexError(RuntimeError):
    """Chroma has no chunks; ingest must be run first."""


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def allowed_source_urls(config: Config) -> set[str]:
    return {source.url for source in config.sources}


def _get_embedder(model_name: str) -> Any:
    global _EMBEDDER, _EMBEDDER_NAME
    if _EMBEDDER is None or _EMBEDDER_NAME != model_name:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError("sentence-transformers is not installed") from exc
        _EMBEDDER = SentenceTransformer(model_name, device="cpu")
        _EMBEDDER_NAME = model_name
    return _EMBEDDER


def _get_collection(config: Config) -> Any:
    global _CHROMA_COLLECTION, _CHROMA_PATH, _CHROMA_NAME
    persist = str(config.chroma_dir)
    if (
        _CHROMA_COLLECTION is None
        or _CHROMA_PATH != persist
        or _CHROMA_NAME != config.collection
    ):
        try:
            import chromadb
        except ImportError as exc:
            raise RuntimeError("chromadb is not installed") from exc
        client = chromadb.PersistentClient(path=persist)
        names = {item.name for item in client.list_collections()}
        if config.collection not in names:
            raise EmptyIndexError("Chroma collection is empty. Please run ingest first.")
        _CHROMA_COLLECTION = client.get_collection(
            name=config.collection,
            embedding_function=None,
        )
        _CHROMA_PATH = persist
        _CHROMA_NAME = config.collection
    return _CHROMA_COLLECTION


@dataclass(frozen=True)
class RetrievalHit:
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


@dataclass(frozen=True)
class RetrievalResult:
    query_id: str
    query: str
    k: int
    hits: list[RetrievalHit]
    trace_path: str
    collection_count: int


def retrieve(query: str, config: Config, query_id: str | None = None) -> RetrievalResult:
    """Retrieve top-k chunks from Chroma for the query and save retrieval trace."""
    if not query_id:
        query_id = uuid.uuid4().hex[:12]

    collection = _get_collection(config)
    total_count = collection.count()
    if total_count == 0:
        raise EmptyIndexError("Chroma collection is empty. Please run ingest first.")

    embedder = _get_embedder(config.embedding_model)
    query_vector = embedder.encode(
        [query],
        normalize_embeddings=True,
        convert_to_numpy=True,
    )[0].tolist()

    k = min(config.retrieval_k, total_count)
    res = collection.query(
        query_embeddings=[query_vector],
        n_results=k,
        include=["distances", "documents", "metadatas"],
    )

    ids = res["ids"][0] if res.get("ids") else []
    distances = res["distances"][0] if res.get("distances") else []
    documents = res["documents"][0] if res.get("documents") else []
    metadatas = res["metadatas"][0] if res.get("metadatas") else []
    allowed = allowed_source_urls(config)

    hits: list[RetrievalHit] = []
    for cid, dist, doc, meta in zip(ids, distances, documents, metadatas):
        meta = meta or {}
        url = str(meta.get("url", ""))
        if url not in allowed:
            continue
        score = float(max(0.0, 1.0 - float(dist)))
        hits.append(
            RetrievalHit(
                chunk_id=str(cid),
                score=round(score, 4),
                distance=round(float(dist), 4),
                text=str(doc),
                url=url,
                title=str(meta.get("title", "")),
                section=str(meta.get("section", "")),
                page_id=str(meta.get("page_id", "")),
                page_type=str(meta.get("page_type", "")),
                scraped_at=str(meta.get("scraped_at", "")),
            )
        )

    trace_file = config.traces_dir / f"{query_id}_retrieval.json"
    write_json(
        trace_file,
        {
            "query_id": query_id,
            "query": query,
            "k": k,
            "collection_count": total_count,
            "timestamp": _now(),
            "hits": [
                {
                    "chunk_id": hit.chunk_id,
                    "score": hit.score,
                    "distance": hit.distance,
                    "url": hit.url,
                    "title": hit.title,
                    "section": hit.section,
                    "page_id": hit.page_id,
                    "page_type": hit.page_type,
                    "scraped_at": hit.scraped_at,
                    "text": hit.text,
                }
                for hit in hits
            ],
        },
    )

    return RetrievalResult(
        query_id=query_id,
        query=query,
        k=k,
        hits=hits,
        trace_path=str(trace_file),
        collection_count=total_count,
    )
