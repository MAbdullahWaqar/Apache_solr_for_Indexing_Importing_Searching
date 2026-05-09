"""Flask backend that proxies search requests to a running Apache Solr core.

Endpoints:
    GET  /api/health        -> Solr ping & document count
    GET  /api/search        -> Full-text search with facets, filters,
                               pagination, sort and highlighting
    GET  /api/suggest       -> Autocomplete suggestions
    GET  /api/facets        -> Standalone facet metadata for the UI sidebar
    GET  /api/book/<id>     -> Single document lookup
    GET  /                  -> Optional convenience: serves frontend/index.html

The Flask app is intentionally thin; the business logic lives in
SolrSearchClient so it remains easy to unit-test and swap.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

from config import config
from search_client import SolrSearchClient

ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = ROOT / "frontend"

app = Flask(__name__, static_folder=None)
CORS(app)
client = SolrSearchClient(config)


# ---------------------------------------------------------------------------
# Health & metadata
# ---------------------------------------------------------------------------
@app.get("/api/health")
def health() -> Any:
    try:
        info = client.health()
        return jsonify({"status": "ok", **info})
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 503


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------
@app.get("/api/search")
def search() -> Any:
    args = request.args

    page = max(1, int(args.get("page", 1)))
    rows = max(1, min(int(args.get("rows", config.page_size_default)),
                      config.page_size_max))
    start = (page - 1) * rows

    query = args.get("q", "").strip() or "*:*"
    sort = args.get("sort", "score desc")

    filters: list[str] = []
    for key in ("genre", "language", "publisher", "tag"):
        for value in args.getlist(key):
            if value:
                field = {
                    "genre": "genres",
                    "language": "language",
                    "publisher": "publisher",
                    "tag": "tags",
                }[key]
                filters.append(f'{field}:"{value}"')

    if args.get("in_stock") in ("1", "true", "yes"):
        filters.append("in_stock:true")

    year_min = args.get("year_min")
    year_max = args.get("year_max")
    if year_min or year_max:
        filters.append(f"year:[{year_min or '*'} TO {year_max or '*'}]")

    rating_min = args.get("rating_min")
    if rating_min:
        filters.append(f"rating:[{rating_min} TO *]")

    try:
        result = client.search(
            query=query,
            filters=filters,
            sort=sort,
            start=start,
            rows=rows,
            highlight=True,
            facets=True,
        )
        result["page"] = page
        result["page_size"] = rows
        return jsonify(result)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


# ---------------------------------------------------------------------------
# Autocomplete
# ---------------------------------------------------------------------------
@app.get("/api/suggest")
def suggest() -> Any:
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"suggestions": []})
    try:
        suggestions = client.suggest(q)
        return jsonify({"suggestions": suggestions})
    except Exception as exc:
        return jsonify({"error": str(exc), "suggestions": []}), 500


# ---------------------------------------------------------------------------
# Facets metadata only (used by the sidebar on initial render)
# ---------------------------------------------------------------------------
@app.get("/api/facets")
def facets() -> Any:
    try:
        return jsonify(client.facets_only())
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


# ---------------------------------------------------------------------------
# Single book lookup
# ---------------------------------------------------------------------------
@app.get("/api/book/<book_id>")
def book(book_id: str) -> Any:
    try:
        doc = client.get(book_id)
        if doc is None:
            return jsonify({"error": "not_found"}), 404
        return jsonify(doc)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


# ---------------------------------------------------------------------------
# Optional convenience: serve the static frontend from the same origin so
# `python backend/app.py` is enough to demo the project end-to-end.
# ---------------------------------------------------------------------------
@app.get("/")
def index() -> Any:
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.get("/favicon.ico")
def favicon() -> Any:
    favicon_path = FRONTEND_DIR / "favicon.ico"
    if favicon_path.exists():
        return send_from_directory(FRONTEND_DIR, "favicon.ico")
    return ("", 204)


@app.get("/<path:filename>")
def static_passthrough(filename: str) -> Any:
    target = FRONTEND_DIR / filename
    if target.exists() and target.is_file():
        return send_from_directory(FRONTEND_DIR, filename)
    return jsonify({"error": "not_found"}), 404


if __name__ == "__main__":
    print(f"Solr base : {config.solr_base}")
    print(f"Flask API : http://{config.flask_host}:{config.flask_port}")
    print(f"Open       http://localhost:{config.flask_port}/  for the bundled UI")
    app.run(host=config.flask_host, port=config.flask_port, debug=config.debug)
