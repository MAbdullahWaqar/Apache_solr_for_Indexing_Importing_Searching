# Backend — Flask + Solr proxy

A small Flask service that exposes a clean JSON API on top of Apache Solr.

## Endpoints

| Method | Path | Description |
| --- | --- | --- |
| GET | `/api/health` | Solr ping + indexed document count |
| GET | `/api/search` | Search with facets, filters, sort, highlighting, pagination |
| GET | `/api/suggest` | Autocomplete suggestions |
| GET | `/api/facets` | Standalone facet metadata (used by the sidebar) |
| GET | `/api/book/<id>` | Single-document lookup |
| GET | `/`, `/index.html`, `/styles.css`, ... | Serves the bundled `frontend/` UI |

### `GET /api/search` parameters

| Param | Type | Notes |
| --- | --- | --- |
| `q` | string | Free-text query; `*:*` if blank |
| `page` | int | 1-indexed page number |
| `rows` | int | Page size, capped at `PAGE_SIZE_MAX` |
| `sort` | string | `score desc`, `rating desc`, `year desc`, ... |
| `genre` | string (repeatable) | `?genre=Programming&genre=Algorithms` |
| `language` | string (repeatable) | |
| `publisher` | string (repeatable) | |
| `tag` | string (repeatable) | |
| `in_stock` | bool | `1`, `true`, or `yes` |
| `year_min`, `year_max` | int | Year range filter |
| `rating_min` | float | Minimum rating |

The response includes `total`, `documents`, `facets.fields`, `facets.ranges`,
`elapsed_ms` and `qtime_ms` for easy benchmarking.

## Configuration

All knobs are environment variables (with sensible defaults):

| Variable | Default | Purpose |
| --- | --- | --- |
| `SOLR_HOST` | `localhost` | |
| `SOLR_PORT` | `8983` | |
| `SOLR_CORE` | `books` | |
| `FLASK_HOST` | `0.0.0.0` | |
| `FLASK_PORT` | `5000` | |
| `FLASK_DEBUG` | `1` | |
| `SOLR_REQUEST_TIMEOUT` | `10.0` | seconds |
| `PAGE_SIZE_DEFAULT` | `12` | |
| `PAGE_SIZE_MAX` | `100` | hard cap |

## Running

```bash
pip install -r backend/requirements.txt
python backend/app.py
# Health: curl http://localhost:5000/api/health
```
