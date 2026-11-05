"""Test retrieval only: embed a question, query Chroma, print top-k hits and the trace path."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import load_config
from app.pipeline.retrieve import EmptyIndexError, retrieve


def main() -> None:
    parser = argparse.ArgumentParser(description="Test Chroma retrieval without calling the LLM.")
    parser.add_argument("question", nargs="+", help="Question to retrieve chunks for")
    parser.add_argument("--full", action="store_true", help="Print each hit's full chunk text")
    args = parser.parse_args()

    question = " ".join(args.question)
    config = load_config()

    try:
        result = retrieve(question, config)
    except EmptyIndexError as exc:
        print(exc, file=sys.stderr)
        raise SystemExit(1)

    print(f"Query: {question}")
    print(f"Collection: {config.collection} | chunks: {result.collection_count} | k: {result.k}")
    print(f"Trace: {result.trace_path}")
    print()

    for rank, hit in enumerate(result.hits, start=1):
        print(f"{rank}. score={hit.score:.4f} distance={hit.distance:.4f}")
        print(f"   chunk_id: {hit.chunk_id}")
        print(f"   section:  {hit.section}")
        print(f"   url:      {hit.url}")
        text = hit.text if args.full else hit.text.replace("\n", " ")[:220]
        print(f"   text:     {text}")
        print()


if __name__ == "__main__":
    main()
