from __future__ import annotations

from app.config import Config, Source
from app.pipeline.artifacts import write_json, write_text
from app.pipeline.fetch import fetch_url
from app.pipeline.parse import html_to_text


def scrape_source(config: Config, source: Source, allowed_urls: set[str]) -> dict:
    result = fetch_url(source.url, allowed_urls)
    metadata = {
        "page_id": source.id,
        "url": source.url,
        "title": source.title,
        "page_type": source.type,
        "http_status": result.status,
        "scraped_at": result.fetched_at,
        "final_url": result.final_url,
        "error": result.error,
        "char_count_text": 0,
        "sparse": False,
        "has_next_data": False,
        "json_ld_count": 0,
    }

    if result.error or not result.html.strip():
        write_json(config.raw_dir / f"{source.id}.metadata.json", metadata)
        return metadata

    text, extras = html_to_text(result.html)
    metadata.update(extras)
    write_text(config.raw_dir / f"{source.id}.html", result.html)
    write_text(config.raw_dir / f"{source.id}.txt", text)
    write_json(config.raw_dir / f"{source.id}.metadata.json", metadata)
    return metadata


def scrape_all(config: Config) -> tuple[list[dict], bool]:
    allowed_urls = {source.url for source in config.sources}
    records: list[dict] = []
    failed = False
    for source in config.sources:
        print(f"Scraping {source.id}: {source.url}")
        metadata = scrape_source(config, source, allowed_urls)
        records.append(metadata)
        if metadata.get("error"):
            failed = True
            print(f"  FAILED {metadata['error']}")
        else:
            print(
                f"  ok status={metadata['http_status']} "
                f"chars={metadata['char_count_text']} sparse={metadata['sparse']}"
            )
    write_json(config.raw_dir / "_index.json", {"pages": records, "source_count": len(config.sources)})
    return records, failed
