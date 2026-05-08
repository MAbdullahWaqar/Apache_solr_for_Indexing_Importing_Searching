# Apache Solr — Indexing, Importing & Searching (Lab 13)

An end-to-end Apache Solr project for the **Parallel and Distributed Computing**
open-ended lab. It demonstrates how to:

- Configure a Solr core with a custom schema, synonyms, and stopwords.
- Bulk-index a real-world **books catalog** dataset (CSV + JSON, 200+ records).
- Run rich search queries — full-text, filtering, sorting, faceting,
  highlighting, and `edismax` with field boosts.
- Expose Solr through a **Flask REST API** with autocomplete, facets, and
  pagination.
- Drive Solr from a **modern, responsive web UI** with real-time search,
  faceted navigation, sort, pagination, and highlighted results.

---

## 1. Repository layout

```
Apache_solr_for_Indexing_Importing_Searching/
├── data/                  # Book catalog (CSV + JSON) and dataset notes
├── solr-config/           # Solr schema, solrconfig snippets, synonyms, stopwords
├── scripts/               # Setup, indexing & sample-query scripts (sh/bat/py)
├── backend/               # Flask API that proxies search calls to Solr
├── frontend/              # Responsive search UI (HTML/CSS/JS)
├── docs/                  # Lab report (markdown + Word generator) and screenshots
├── examples/              # Sample queries, performance observations
└── README.md
```

## 2. Quick start

> Prerequisites: **Apache Solr 9.x** and **Python 3.9+**. A bundled Solr is
> *not* committed; install Solr separately (`brew install solr`, the official
> tarball, or the Windows `.zip`).

### 2.1 Start Solr and create the `books` core

```bash
# Start Solr in the foreground or as a service
solr start -p 8983

# Create the core named "books"
solr create -c books

# Apply the custom schema (managed-schema fields, copyFields, suggester)
bash scripts/apply_schema.sh
```

On Windows use the `.bat` equivalents in `scripts/`.

### 2.2 Index the dataset

```bash
# Option A: cURL (Solr's native /update handler)
bash scripts/index_data.sh

# Option B: Python client (pysolr)
pip install -r backend/requirements.txt
python scripts/index_data.py
```

### 2.3 Run the web app

```bash
# Backend
pip install -r backend/requirements.txt
python backend/app.py            # http://localhost:5000

# Frontend (no build step required)
# Open frontend/index.html in your browser, or serve it:
python -m http.server 8000 --directory frontend
# then visit http://localhost:8000
```

## 3. Features at a glance

| Area | Capability |
| --- | --- |
| **Schema** | 14 typed fields (text, string, int, float, date, multivalued tags), copyFields into `_text_`, suggester component for autocomplete. |
| **Indexing** | CSV (`/update/csv`) and JSON (`/update/json/docs`) ingestion paths, atomic-update friendly. |
| **Querying** | `edismax` with field boosting (`title^5 author^3 description^1`). |
| **Filtering** | `fq` filter queries on genre, language, year range, in-stock. |
| **Faceting** | Genre, author, language, decade range facets. |
| **Highlighting** | `<mark>` tags on title and description. |
| **Sorting** | By relevance, year, rating, price, title. |
| **Pagination** | `start` / `rows` with total-count metadata. |
| **Autocomplete** | `/suggest` endpoint backed by Solr's Suggester. |
| **UI** | Responsive layout, dark theme, debounced live search, facet sidebar. |

## 4. Documentation & deliverables

- `docs/Lab_13_Report.md` — full lab write-up (problem statement, dataset, config, implementation, observations, challenges, conclusion).
- `docs/generate_report.py` — produces a Word `.docx` from the markdown report.
- `examples/queries.md` — 25+ illustrative Solr queries.
- `examples/observations.md` — performance and accuracy notes.

## 5. License

This repository is published for educational purposes as part of the PDC course
at FAST-NUCES.
