from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Source:
    id: str
    type: str
    title: str
    url: str


@dataclass(frozen=True)
class Config:
    raw_dir: Path
    loaded_dir: Path
    chunks_dir: Path
    embeddings_dir: Path
    traces_dir: Path
    chroma_dir: Path
    collection: str
    distance: str
    embedding_model: str
    retrieval_k: int
    retrieval_min_score: float
    llm_provider: str
    llm_temperature: float
    chunking: dict[str, Any]
    sources: list[Source]
    educational_links: list[dict[str, Any]]


def load_config() -> Config:
    load_dotenv(ROOT / ".env")
    with (ROOT / "config.yaml").open(encoding="utf-8") as fh:
        raw = yaml.safe_load(fh)

    paths = raw["paths"]
    vector_db = raw["vector_db"]
    sources = [Source(**item) for item in raw["sources"]]

    return Config(
        raw_dir=ROOT / paths["raw"],
        loaded_dir=ROOT / paths["loaded"],
        chunks_dir=ROOT / paths["chunks"],
        embeddings_dir=ROOT / paths["embeddings"],
        traces_dir=ROOT / paths["traces"],
        chroma_dir=ROOT / vector_db["persist_dir"],
        collection=vector_db["collection"],
        distance=vector_db["distance"],
        embedding_model=raw["embedding_model"],
        retrieval_k=int(raw["retrieval"]["k"]),
        retrieval_min_score=float(raw["retrieval"].get("min_score", 0.55)),
        llm_provider=raw["llm"]["provider"],
        llm_temperature=float(raw["llm"]["temperature"]),
        chunking=raw["chunking"],
        sources=sources,
        educational_links=list(raw.get("educational_links") or []),
    )


def ensure_dirs(config: Config) -> list[Path]:
    created: list[Path] = []
    for path in (
        config.raw_dir,
        config.loaded_dir,
        config.chunks_dir,
        config.embeddings_dir,
        config.traces_dir,
        config.chroma_dir,
    ):
        path.mkdir(parents=True, exist_ok=True)
        created.append(path)
    return created
