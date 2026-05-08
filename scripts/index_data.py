"""Bulk-index data/books.json into a running Solr core using pysolr.

Run:
    pip install -r backend/requirements.txt
    python scripts/index_data.py
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

import pysolr  # type: ignore[import-not-found]

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "books.json"

SOLR_HOST = os.environ.get("SOLR_HOST", "localhost")
SOLR_PORT = int(os.environ.get("SOLR_PORT", "8983"))
CORE_NAME = os.environ.get("CORE_NAME", "books")
SOLR_URL = f"http://{SOLR_HOST}:{SOLR_PORT}/solr/{CORE_NAME}"


def main() -> None:
    if not DATA_FILE.exists():
        raise SystemExit(
            f"Dataset not found: {DATA_FILE}\n"
            "Run `python scripts/generate_dataset.py` first."
        )

    with DATA_FILE.open(encoding="utf-8") as fh:
        records = json.load(fh)

    print(f"Connecting to {SOLR_URL}")
    client = pysolr.Solr(SOLR_URL, always_commit=False, timeout=15)

    print(f"Posting {len(records)} documents...")
    started = time.perf_counter()
    client.add(records)
    client.commit()
    elapsed = time.perf_counter() - started
    print(f"Indexed {len(records)} docs in {elapsed:.2f}s "
          f"({len(records) / elapsed:.0f} docs/s)")

    total = client.search("*:*", rows=0).hits
    print(f"Total documents in core: {total}")


if __name__ == "__main__":
    main()
