"""Runtime configuration for the Flask backend.

All settings can be overridden via environment variables, which keeps the
container/cloud story simple and never hard-codes secrets in source.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    solr_host: str = os.environ.get("SOLR_HOST", "localhost")
    solr_port: int = int(os.environ.get("SOLR_PORT", "8983"))
    solr_core: str = os.environ.get("SOLR_CORE", "books")
    flask_host: str = os.environ.get("FLASK_HOST", "0.0.0.0")
    flask_port: int = int(os.environ.get("FLASK_PORT", "5000"))
    debug: bool = os.environ.get("FLASK_DEBUG", "1") == "1"

    request_timeout_seconds: float = float(
        os.environ.get("SOLR_REQUEST_TIMEOUT", "10.0")
    )
    page_size_default: int = int(os.environ.get("PAGE_SIZE_DEFAULT", "12"))
    page_size_max: int = int(os.environ.get("PAGE_SIZE_MAX", "100"))

    @property
    def solr_base(self) -> str:
        return f"http://{self.solr_host}:{self.solr_port}/solr/{self.solr_core}"


config = Config()
