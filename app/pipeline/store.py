"""Phase 6: upsert embedded chunks into a persistent Chroma collection."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

import numpy as np

from app.config import Config

BATCH_SIZE = 128
METADATA_FIELDS = ("url", "title", "section", "page_id", "page_type", "scraped_at")


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


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
            missing = [field for field in METADATA_FIELDS if not row.get(field)]
            if missing:
                return [], f"{chunk_id}: missing metadata {missing}"
            rows.append(row)
            page_count += 1

        if page_count == 0:
            return [], f"no chunks in {path.name}"
        print(f"  {source.id}: {page_count} chunks")

    ids = [row["chunk_id"] for row in rows]
    if len(ids) != len(set(ids)):
        return [], "duplicate chunk_id values across chunk files"
    return rows, None


def _load_embeddings(
    config: Config, chunk_ids: list[str]
) -> tuple[np.ndarray | None, dict[str, Any] | None, str | None]:
    manifest_path = config.embeddings_dir / "manifest.json"
    ids_path = config.embeddings_dir / "ids.json"
    vectors_path = config.embeddings_dir / "vectors.npy"
    for path in (manifest_path, ids_path, vectors_path):
        if not path.exists():
            return None, None, f"missing embedding artifact: {path.name}"

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        ids = json.loads(ids_path.read_text(encoding="utf-8"))
        vectors = np.load(vectors_path, allow_pickle=False)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return None, None, f"unreadable embedding artifacts: {exc}"

    if not isinstance(manifest, dict):
        return None, None, "manifest.json is not an object"
    if manifest.get("model") != config.embedding_model:
        return (
            None,
            None,
            "embedding model changed since embed; re-run load -> chunk -> embed",
        )
    if not isinstance(ids, list) or ids != chunk_ids:
        return None, None, "ids.json does not match current chunk order; re-run embed"

    vectors = np.asarray(vectors, dtype=np.float32)
    if vectors.ndim != 2 or vectors.shape[0] != len(ids):
        return None, None, f"unexpected vectors shape: {vectors.shape}"
    if manifest.get("count") != len(ids):
        return None, None, "manifest count does not match ids"
    if manifest.get("dimension") != int(vectors.shape[1]):
        return None, None, "manifest dimension does not match vectors"
    if not np.isfinite(vectors).all():
        return None, None, "vectors contain non-finite values"
    norms = np.linalg.norm(vectors, axis=1)
    if not np.allclose(norms, 1.0, atol=1e-3):
        return None, None, "vectors are not normalized; re-run embed"

    return vectors, manifest, None


def _load_client(config: Config) -> Any:
    try:
        import chromadb
    except ImportError as exc:
        raise RuntimeError(
            "chromadb is not installed; run "
            "`.venv\\Scripts\\python.exe -m pip install -r requirements.txt`"
        ) from exc
    return chromadb.PersistentClient(path=str(config.chroma_dir))


def _get_collection(client: Any, config: Config, manifest: dict[str, Any]) -> Any:
    existing = next(
        (item for item in client.list_collections() if item.name == config.collection),
        None,
    )
    recreate = False
    if existing is not None:
        metadata = existing.metadata or {}
        configuration = getattr(existing, "configuration_json", {}) or {}
        space = (configuration.get("hnsw") or {}).get("space")
        recreate = (
            metadata.get("embedding_model") != config.embedding_model
            or metadata.get("dimension") != int(manifest["dimension"])
            or metadata.get("distance") != config.distance
            or space != config.distance
        )
        if recreate:
            print("  rebuilding collection: embedding model or distance changed")
            client.delete_collection(name=config.collection)

    if existing is None or recreate:
        return client.create_collection(
            name=config.collection,
            configuration={"hnsw": {"space": config.distance}},
            metadata={
                "embedding_model": config.embedding_model,
                "dimension": int(manifest["dimension"]),
                "distance": config.distance,
                "created_at": _now(),
            },
            embedding_function=None,
        )
    return client.get_collection(name=config.collection, embedding_function=None)


def _metadata(row: dict[str, Any]) -> dict[str, str]:
    return {field: str(row[field]) for field in METADATA_FIELDS}


def store_all(config: Config) -> tuple[list[dict[str, Any]], bool]:
    print(f"Storing chunks in Chroma collection {config.collection}")
    rows, error = _read_chunks(config)
    if error:
        print(f"  FAILED {error}")
        return [], True

    ids = [row["chunk_id"] for row in rows]
    vectors, manifest, error = _load_embeddings(config, ids)
    if error or vectors is None or manifest is None:
        print(f"  FAILED {error}")
        return [], True

    try:
        client = _load_client(config)
        collection = _get_collection(client, config, manifest)
    except Exception as exc:
        print(f"  FAILED opening Chroma collection: {exc}")
        return [], True

    try:
        for start in range(0, len(rows), BATCH_SIZE):
            batch = rows[start : start + BATCH_SIZE]
            collection.upsert(
                ids=[row["chunk_id"] for row in batch],
                embeddings=vectors[start : start + BATCH_SIZE].tolist(),
                documents=[row["text"] for row in batch],
                metadatas=[_metadata(row) for row in batch],
            )
        stored_ids = set(collection.get(include=[]).get("ids") or [])
        stale_ids = sorted(stored_ids - set(ids))
        if stale_ids:
            collection.delete(ids=stale_ids)
            print(f"  removed stale ids: {len(stale_ids)}")
            stored_ids -= set(stale_ids)

        count = collection.count()
        if stored_ids != set(ids) or count != len(ids):
            print(f"  FAILED collection count={count}, expected={len(ids)}")
            return [], True
    except Exception as exc:
        print(f"  FAILED writing Chroma collection: {exc}")
        return [], True

    print(f"  ok collection={config.collection} count={count}")
    return (
        [
            {
                "collection": config.collection,
                "count": count,
                "persist_dir": str(config.chroma_dir),
            }
        ],
        False,
    )
