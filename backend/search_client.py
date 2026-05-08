"""Thin wrapper around Solr's REST API used by the Flask app.

Why a thin wrapper instead of `pysolr` for queries?
    * We need full control over edismax parameters, multiple `fq` filters,
      pluggable facets, JSON-API response, and the Suggester.
    * Keeping the surface focused on the four endpoints the UI needs makes the
      code easy to read and test.
"""

from __future__ import annotations

import time
from typing import Any

import requests

from config import Config


class SolrSearchClient:
    """High-level helpers for the Flask app."""

    def __init__(self, cfg: Config) -> None:
        self.cfg = cfg
        self.base = cfg.solr_base
        self.timeout = cfg.request_timeout_seconds
        self._session = requests.Session()

    # ------------------------------------------------------------------ #
    # Health / metadata
    # ------------------------------------------------------------------ #
    def health(self) -> dict[str, Any]:
        ping = self._get("admin/ping", {"wt": "json"})
        total = self._get("select", {"q": "*:*", "rows": 0}).get(
            "response", {}
        ).get("numFound", 0)
        return {
            "solr": ping.get("status", "unknown"),
            "core": self.cfg.solr_core,
            "documents": total,
            "base_url": self.base,
        }

    # ------------------------------------------------------------------ #
    # Search
    # ------------------------------------------------------------------ #
    def search(
        self,
        *,
        query: str,
        filters: list[str],
        sort: str,
        start: int,
        rows: int,
        highlight: bool,
        facets: bool,
    ) -> dict[str, Any]:
        params: list[tuple[str, Any]] = [
            ("q", query),
            ("defType", "edismax"),
            ("qf", "title^5 author^3 tags^2 description^1 _text_^0.5"),
            ("pf", "title^10 description^2"),
            ("mm", "2<-1 5<75%"),
            ("tie", "0.1"),
            ("q.alt", "*:*"),
            ("start", start),
            ("rows", rows),
            ("sort", sort),
            (
                "fl",
                "id,title,author,genres,language,year,pages,rating,price,"
                "in_stock,stock_count,publisher,isbn,pub_date,tags,description,score",
            ),
            ("wt", "json"),
        ]
        for fq in filters:
            params.append(("fq", fq))

        if highlight:
            params.extend([
                ("hl", "true"),
                ("hl.fl", "title,description"),
                ("hl.simple.pre", "<mark>"),
                ("hl.simple.post", "</mark>"),
                ("hl.fragsize", 220),
            ])

        if facets:
            params.extend([
                ("facet", "true"),
                ("facet.mincount", 1),
                ("facet.limit", 15),
                ("facet.field", "genres"),
                ("facet.field", "language"),
                ("facet.field", "publisher"),
                ("facet.field", "tags"),
                ("facet.range", "year"),
                ("facet.range.start", 1700),
                ("facet.range.end", 2030),
                ("facet.range.gap", 10),
            ])

        started = time.perf_counter()
        raw = self._get("select", params)
        elapsed_ms = round((time.perf_counter() - started) * 1000, 1)

        response = raw.get("response", {})
        docs = response.get("docs", [])
        highlighting = raw.get("highlighting", {})

        for doc in docs:
            hl = highlighting.get(doc.get("id"), {})
            if hl:
                doc["_highlight"] = hl

        facet_counts = raw.get("facet_counts", {})

        return {
            "total": response.get("numFound", 0),
            "start": response.get("start", 0),
            "rows": rows,
            "elapsed_ms": elapsed_ms,
            "qtime_ms": raw.get("responseHeader", {}).get("QTime", 0),
            "documents": docs,
            "facets": _normalize_facets(facet_counts),
            "query": query,
            "filters": filters,
            "sort": sort,
        }

    # ------------------------------------------------------------------ #
    # Suggester
    # ------------------------------------------------------------------ #
    def suggest(self, q: str) -> list[dict[str, Any]]:
        """Return autocomplete suggestions.

        Tries Solr's Suggester component first; if the dictionary is missing
        (e.g. the user has not added the /suggest handler) it transparently
        falls back to a prefix query against `title_ac`.
        """

        try:
            raw = self._get(
                "suggest",
                {
                    "suggest": "true",
                    "suggest.q": q,
                    "suggest.dictionary": ["titleSuggester", "authorSuggester"],
                    "suggest.count": 8,
                    "wt": "json",
                },
            )
            suggestions: list[dict[str, Any]] = []
            seen: set[str] = set()
            blocks = raw.get("suggest", {})
            for dict_name, value in blocks.items():
                inner = value.get(q, {}) or value.get(q.lower(), {})
                for s in inner.get("suggestions", []):
                    term = s.get("term") or ""
                    if not term or term.lower() in seen:
                        continue
                    seen.add(term.lower())
                    suggestions.append(
                        {"term": term, "weight": s.get("weight", 0),
                         "source": dict_name}
                    )
            if suggestions:
                return suggestions
        except Exception:
            pass

        # Fallback: prefix query
        raw = self._get(
            "select",
            {
                "q": f"title_ac:{_escape_solr(q)}*",
                "rows": 8,
                "fl": "title,author,id",
                "wt": "json",
            },
        )
        results: list[dict[str, Any]] = []
        for doc in raw.get("response", {}).get("docs", []):
            results.append({
                "term": doc.get("title"),
                "id": doc.get("id"),
                "source": "fallback",
            })
        return results

    # ------------------------------------------------------------------ #
    # Facets only (used by the sidebar before the user types anything)
    # ------------------------------------------------------------------ #
    def facets_only(self) -> dict[str, Any]:
        params: list[tuple[str, Any]] = [
            ("q", "*:*"),
            ("rows", 0),
            ("facet", "true"),
            ("facet.mincount", 1),
            ("facet.limit", 25),
            ("facet.field", "genres"),
            ("facet.field", "language"),
            ("facet.field", "publisher"),
            ("facet.field", "tags"),
            ("facet.range", "year"),
            ("facet.range.start", 1700),
            ("facet.range.end", 2030),
            ("facet.range.gap", 10),
            ("wt", "json"),
        ]
        raw = self._get("select", params)
        return {
            "total": raw.get("response", {}).get("numFound", 0),
            "facets": _normalize_facets(raw.get("facet_counts", {})),
        }

    # ------------------------------------------------------------------ #
    # Single document lookup
    # ------------------------------------------------------------------ #
    def get(self, doc_id: str) -> dict[str, Any] | None:
        raw = self._get(
            "select",
            {"q": f"id:{_escape_solr(doc_id)}", "rows": 1, "wt": "json"},
        )
        docs = raw.get("response", {}).get("docs", [])
        return docs[0] if docs else None

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    def _get(self, handler: str, params: Any) -> dict[str, Any]:
        url = f"{self.base}/{handler}"
        resp = self._session.get(url, params=params, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()


# ---------------------------------------------------------------------------
# Module helpers
# ---------------------------------------------------------------------------
def _normalize_facets(facet_counts: dict[str, Any]) -> dict[str, Any]:
    """Reshape Solr's facet response into a friendlier structure."""

    fields_raw = facet_counts.get("facet_fields", {}) or {}
    fields: dict[str, list[dict[str, Any]]] = {}
    for field, items in fields_raw.items():
        pairs: list[dict[str, Any]] = []
        for i in range(0, len(items), 2):
            label = items[i]
            count = items[i + 1] if i + 1 < len(items) else 0
            if not label:
                continue
            pairs.append({"value": label, "count": count})
        fields[field] = pairs

    ranges_raw = facet_counts.get("facet_ranges", {}) or {}
    ranges: dict[str, dict[str, Any]] = {}
    for field, payload in ranges_raw.items():
        counts_list = payload.get("counts", [])
        buckets = []
        for i in range(0, len(counts_list), 2):
            label = counts_list[i]
            count = counts_list[i + 1] if i + 1 < len(counts_list) else 0
            buckets.append({"value": label, "count": count})
        ranges[field] = {
            "start": payload.get("start"),
            "end": payload.get("end"),
            "gap": payload.get("gap"),
            "buckets": buckets,
        }

    return {"fields": fields, "ranges": ranges}


def _escape_solr(value: str) -> str:
    """Escape Solr query syntax characters that would otherwise be reserved."""

    reserved = r'+-&|!(){}[]^"~*?:\\/'
    return "".join("\\" + c if c in reserved else c for c in value)
