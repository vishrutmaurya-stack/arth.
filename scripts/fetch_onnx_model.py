"""Fetch the pinned fp32 ONNX export of all-MiniLM-L6-v2 into models/.

Run at Render build time (or locally once):
    python scripts/fetch_onnx_model.py

The files are byte-identical to the Hugging Face revision the existing
embeddings were generated from, so the 152 stored vectors stay valid.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REVISION = "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"
BASE = (
    "https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2"
    f"/resolve/{REVISION}"
)

# local name -> (remote path, sha256 of the pinned revision)
FILES = {
    "model.onnx": (
        "onnx/model.onnx",
        "6fd5d72fe4589f189f8ebc006442dbb529bb7ce38f8082112682524616046452",
    ),
    "tokenizer.json": (
        "tokenizer.json",
        "be50c3628f2bf5bb5e3a7f17b1f74611b2561a3a27eeab05e5aa30f411572037",
    ),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def download(url: str, target: Path) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": "arth-ai-build"})
    last_error: Exception | None = None
    for attempt in range(1, 4):
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                with target.open("wb") as fh:
                    for chunk in iter(lambda: response.read(1024 * 1024), b""):
                        fh.write(chunk)
            return
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_error = exc
            target.unlink(missing_ok=True)
            if attempt < 3:
                print(f"  attempt {attempt} failed ({exc}); retrying...")
                time.sleep(2)
    raise SystemExit(f"download failed: {last_error}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dest",
        type=Path,
        default=ROOT / "models",
        help="output directory (default: <repo>/models)",
    )
    parser.add_argument("--force", action="store_true", help="re-download even if present")
    args = parser.parse_args()

    dest: Path = args.dest
    dest.mkdir(parents=True, exist_ok=True)

    for local_name, (remote_path, expected) in FILES.items():
        target = dest / local_name
        if target.exists() and not args.force:
            actual = sha256(target)
            if actual == expected:
                print(f"ok {target} ({target.stat().st_size / 1048576:.1f} MB)")
                continue
            print(f"hash mismatch for {target}; re-downloading")

        url = f"{BASE}/{remote_path}"
        print(f"downloading {local_name} from {url}")
        temp = target.with_name(target.name + ".part")
        download(url, temp)
        actual = sha256(temp)
        if actual != expected:
            temp.unlink(missing_ok=True)
            raise SystemExit(f"hash mismatch for {local_name}: {actual}")
        temp.replace(target)
        print(f"saved {target} ({target.stat().st_size / 1048576:.1f} MB)")

    print(f"ONNX model ready in {dest}")


if __name__ == "__main__":
    main()
