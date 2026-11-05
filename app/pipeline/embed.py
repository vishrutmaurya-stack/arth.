"""Phase 5: embed chunk text with the configured sentence-transformers model."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

import numpy as np

from app.config import Config
from app.pipeline.artifacts import write_json

BATCH_SIZE = 32


def _read_chunks(config: Config) -> tuple[list[dict[str, Any]], str | None]:
    rows: list[dict[str, Any]] = []
    for source in config.sources:
        path = config.chunks_dir / f"{source.id}.jsonl"
        if not path.exists():
            return [], f"missing chunk file: {path.name}"
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            return [], f"unreadable chunk file {path.name}: {exc}"

        page_count = 0
        for line_number, line in enumerate(lines, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                return [], f"{path.name} line {line_number}: invalid JSON: {exc}"
            if not isinstance(row, dict):
                return [], f"{path.name} line {line_number}: chunk is not an object"
            chunk_id = row.get("chunk_id")
            if not isinstance(chunk_id, str) or not chunk_id:
                return [], f"{path.name} line {line_number}: missing chunk_id"
            text = row.get("text")
            if not isinstance(text, str) or not text.strip():
                return [], f"{path.name} line {line_number}: empty chunk text"
            rows.append(row)
            page_count += 1

        if page_count == 0:
            return [], f"no chunks in {path.name}"
        print(f"  {source.id}: {page_count} chunks")

    ids = [row["chunk_id"] for row in rows]
    if len(ids) != len(set(ids)):
        return [], "duplicate chunk_id values across chunk files"
    return rows, None


def _embedding_text(row: dict[str, Any]) -> str:
    """Keep the page title in the vector so scheme facts are distinguishable."""
    title = str(row.get("title") or "").strip()
    text = str(row.get("text") or "").strip()
    return f"{title}\n{text}" if title else text


def _load_model(model_name: str) -> Any:
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise RuntimeError(
            "sentence-transformers is not installed; run "
            "`.venv\\Scripts\\python.exe -m pip install -r requirements.txt`"
        ) from exc
    return SentenceTransformer(model_name, device="cpu")


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _clear_outputs(config: Config) -> None:
    for name in ("manifest.json", "ids.json", "vectors.npy"):
        (config.embeddings_dir / name).unlink(missing_ok=True)


def embed_all(config: Config) -> tuple[list[dict[str, Any]], bool]:
    print(f"Embedding chunks with {config.embedding_model}")
    rows, error = _read_chunks(config)
    if error:
        print(f"  FAILED {error}")
        return [], True

    ids = [row["chunk_id"] for row in rows]
    texts = [_embedding_text(row) for row in rows]

    try:
        model = _load_model(config.embedding_model)
        vectors = model.encode(
            texts,
            batch_size=BATCH_SIZE,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
    except Exception as exc:  # model download/load/encode failures
        print(f"  FAILED embedding model: {exc}")
        return [], True

    vectors = np.asarray(vectors, dtype=np.float32)
    if vectors.ndim != 2 or vectors.shape[0] != len(ids):
        print(f"  FAILED unexpected embedding shape: {vectors.shape}")
        return [], True
    if not np.isfinite(vectors).all():
        print("  FAILED embeddings contain non-finite values")
        return [], True

    # Normalize again so cosine distance is exact even if the model normalizer changes.
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    if np.any(norms <= 0):
        print("  FAILED embeddings contain a zero vector")
        return [], True
    vectors = vectors / norms

    dimension = int(vectors.shape[1])
    per_page: list[dict[str, Any]] = []
    for source in config.sources:
        count = sum(1 for row in rows if row.get("page_id") == source.id)
        per_page.append({"page_id": source.id, "chunks": count})

    _clear_outputs(config)
    np.save(config.embeddings_dir / "vectors.npy", vectors)
    write_json(config.embeddings_dir / "ids.json", ids)
    write_json(
        config.embeddings_dir / "manifest.json",
        {
            "model": config.embedding_model,
            "dimension": dimension,
            "count": len(ids),
            "embedding_input": "title + chunk text",
            "normalized": True,
            "distance": config.distance,
            "chunking_strategy": config.chunking.get("strategy", "section_fact"),
            "created_at": _now(),
            "vectors_file": "vectors.npy",
            "ids_file": "ids.json",
            "pages": per_page,
        },
    )

    print(f"  ok model={config.embedding_model} dim={dimension} count={len(ids)}")
    return (
        [{"model": config.embedding_model, "dimension": dimension, "count": len(ids)}],
        False,
    )
