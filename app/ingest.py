"""Ingest CLI: scrape → load → chunk → embed → chroma."""

from __future__ import annotations

import argparse
import sys

from app.config import ensure_dirs, load_config
from app.pipeline.chunk import chunk_all
from app.pipeline.embed import embed_all
from app.pipeline.load import load_all
from app.pipeline.scrape import scrape_all
from app.pipeline.store import store_all

PHASES = ["scrape", "load", "chunk", "embed", "store"]


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest Groww source pages.")
    parser.add_argument(
        "--phase",
        choices=PHASES,
        default="scrape",
        help="Run one phase (scrape, load, chunk, embed, or store).",
    )
    parser.add_argument(
        "--from-phase",
        choices=PHASES,
        default=None,
        help="Start at this phase and run the remaining implemented phases.",
    )
    args = parser.parse_args()

    config = load_config()
    ensure_dirs(config)
    print(f"Sources ({len(config.sources)}):")
    for source in config.sources:
        print(f"  - {source.id} [{source.type}] {source.url}")

    if args.from_phase:
        phases = PHASES[PHASES.index(args.from_phase) :]
    else:
        phases = [args.phase]

    for phase in phases:
        if phase == "scrape":
            _, failed = scrape_all(config)
            if failed:
                print("Scrape finished with errors. See data/raw/*.metadata.json")
                sys.exit(1)
            print("Scrape complete. Files are in data/raw/")
        elif phase == "load":
            _, failed = load_all(config)
            if failed:
                print("Load finished with errors. See data/loaded/_index.json")
                sys.exit(1)
            print("Load complete. Files are in data/loaded/")
        elif phase == "chunk":
            _, failed = chunk_all(config)
            if failed:
                print("Chunk finished with errors. See data/chunks/_index.json")
                sys.exit(1)
            print("Chunk complete. Files are in data/chunks/")
        elif phase == "embed":
            _, failed = embed_all(config)
            if failed:
                print("Embed finished with errors. See data/embeddings/")
                sys.exit(1)
            print("Embed complete. Files are in data/embeddings/")
        elif phase == "store":
            _, failed = store_all(config)
            if failed:
                print("Store finished with errors. See data/embeddings/ and chroma/")
                sys.exit(1)
            print("Store complete. Collection is in chroma/")


if __name__ == "__main__":
    main()
