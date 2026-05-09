# Lab 13 — Open-Ended Lab: Indexing, Importing and Searching data in Apache Solr

**Course:** Parallel and Distributed Computing  
**Author:** Muhammad Abdullah Waqar  
**GitHub:** <https://github.com/MAbdullahWaqar/Apache_solr_for_Indexing_Importing_Searching>

---

## 1. Problem Statement

Apache Solr is a high-performance, open-source full-text search platform built
on Apache Lucene. It is used by a wide range of organisations to power
e-commerce search, log analytics, enterprise intranets, and other workloads
that need fast, scalable, faceted retrieval over large amounts of structured
or semi-structured text.

The objective of this lab is to demonstrate, end to end, how to:

1. **Configure** an Apache Solr core with a custom schema.
2. **Index** a real-world dataset using both the `/update/csv` and
   `/update/json/docs` handlers.
3. **Search** that data with rich queries — full-text, filtered, sorted,
   faceted, and highlighted.
4. **Expose** the search functionality through a web application that any
   non-technical user can interact with.

The deliverable is a working, reproducible project (this repository) plus this
report describing the dataset, configuration, implementation, observations
and conclusions.

---

## 2. Dataset Description

### 2.1 Choice of dataset

I chose a **books catalog** because:

- It contains a healthy mix of *text* (title, author, description), *categorical*
  (genre, language, publisher), *numeric* (year, pages, price, rating) and
  *boolean* (in stock) fields. This lets the project demonstrate text search,
  range queries, faceting, sorting and filtering without contrivance.
- The schema is intuitive — anyone can understand what a *book* is — so the
  search UI is immediately usable in a demo.
- The dataset is small enough to ship in the repo (under 1 MB) but large enough
  (250 documents) to make pagination, faceting and decade-range bucketing
  meaningful.

### 2.2 Generation

The catalogue is produced deterministically by
`scripts/generate_dataset.py`. Approximately **85 hand-curated seed books**
across programming, software engineering, distributed systems, fiction,
business, biography and science are recombined into ~250 records (companion
volumes, workbooks, annotated editions, etc.) using a fixed random seed so the
output is reproducible across machines.

The two on-disk artefacts are:

| File | Records | Purpose |
| --- | --- | --- |
| `data/books.csv` | 250 | Indexed via `/update?` (Solr's CSV handler) |
| `data/books.json` | 250 | Indexed via `/update/json/docs` |

### 2.3 Schema

| Field | Solr type | Multi-valued | Notes |
| --- | --- | --- | --- |
| `id` | `string` | no | Unique key |
| `title` | `text_general` | no | Full-text + copied to `_text_`, `title_str`, `title_ac` |
| `author` | `text_general` | no | Full-text + copied to `_text_`, `author_str` |
| `genres` | `strings` | yes | Faceted |
| `language` | `string` | no | Faceted |
| `year` | `pint` | no | Range queries / sort |
| `pages` | `pint` | no | Range queries |
| `rating` | `pfloat` | no | Range queries / sort |
| `price` | `pfloat` | no | Range queries / sort |
| `in_stock` | `boolean` | no | Filter |
| `stock_count` | `pint` | no | Range queries |
| `publisher` | `string` | no | Faceted |
| `isbn` | `string` | no | Lookup |
| `pub_date` | `pdate` | no | Date range / sort |
| `tags` | `strings` | yes | Faceted |
| `description` | `text_general` | no | Highlighted |

`copyField` directives funnel `title`, `author`, `description`, `genres` and
`tags` into the catch-all `_text_` field for default queries, plus
`title -> title_ac` for the autocomplete edge-n-gram analyzer.

---

## 3. Configuration Details

### 3.1 Solr installation and SolrCloud cluster

- **Solr version:** 9.5.0
- **Recommended mode for this lab:** SolrCloud on a single machine
- **Node 1:** `localhost:8983`
- **Node 2:** `localhost:7574`
- **Embedded ZooKeeper:** `localhost:9983`
- **Collection name:** `books`
- **Shards:** 2
- **Replication factor:** 2

The project includes `scripts/setup_solrcloud.sh`, which creates a real
two-node SolrCloud cluster on one host. The collection has two logical shards
and two replicas, giving four physical cores distributed across the two Solr
nodes. This satisfies the lab prerequisite to create a cluster of servers
(shards) while remaining easy to reproduce on a laptop.

For a simpler non-cloud demonstration, `scripts/setup_solr.sh` can create a
standalone `books` core, but the screenshots and final evaluation use
SolrCloud mode.

### 3.2 Schema strategy

Rather than editing `managed-schema` by hand, the project ships
`scripts/apply_schema.sh` which uses Solr's **Schema API** to push the field
types, fields and copyFields. Before the schema is applied,
`scripts/install_resources.sh` copies `synonyms.txt` and `stopwords.txt` into
the active core configuration (standalone) or into ZooKeeper (SolrCloud). This
ensures that the `text_en` analyzer can resolve the custom synonym and stopword
resources.

A reference XML schema (`solr-config/managed-schema.xml`) is also checked in
for documentation and review.

### 3.3 Field-type strategy

Three custom-tuned types complement the Solr defaults:

- **`text_en`** — Standard tokenizer + stop filter + lower-case +
  English-possessive + Porter stemmer. Synonyms are applied at *query time
  only* so the index stays compact.
- **`text_suggest`** — Edge-n-gram (2..20) analyzer used for the autocomplete
  field `title_ac`.
- **Point fields (`pint`, `pfloat`, `pdate`)** — All numeric/date fields use
  `docValues=true` to enable cheap faceting, sorting and range queries.

### 3.4 Request handlers

The `/select` handler is configured with sensible project defaults:

- `defType=edismax` with `qf="title^5 author^3 tags^2 description^1 _text_^0.5"`
- `pf="title^10 description^2"` for phrase boosting
- `mm="2<-1 5<75%"` (relax minimum-should-match for short queries)
- Highlighting on `title` and `description` with `<mark>` tags
- Default facet fields: `genres`, `language`, `publisher`, `tags`
- A `year` range facet from 1700 to 2030 in 10-year buckets

Autocomplete is implemented in two layers. If a Solr `/suggest` handler is
configured, the backend uses it. If not, the backend falls back to the
`title_ac` edge-ngram field, so autocomplete still works in a fresh Solr 10
setup without manual `solrconfig.xml` editing. Spellcheck-style demonstrations
are included through query examples.

---

## 4. Implementation Steps

The project is split into four focused folders:

```
data/        - CSV + JSON dataset and a deterministic generator
solr-config/ - Schema, request-handler snippets, synonyms, stopwords
scripts/     - Cross-platform setup, schema, indexing & sample-query scripts
backend/    - Flask API that proxies search requests to Solr
frontend/    - Responsive HTML/CSS/JS search UI
```

### Step 1 — Install Solr

On macOS:

```bash
brew install solr
```

On Windows: download the `.zip` from <https://solr.apache.org/downloads.html>,
extract it, and add `bin\` to `PATH`.

### Step 2 — Start Solr & create the core

```bash
bash scripts/setup_solrcloud.sh
```

This idempotent script starts Solr node 1 on port 8983, Solr node 2 on port
7574, launches embedded ZooKeeper, and creates the `books` collection with
2 shards and replication factor 2.

### Step 3 — Generate & index the dataset

```bash
python3 scripts/generate_dataset.py     # writes data/books.csv & .json
bash   scripts/install_resources.sh     # pushes synonyms/stopwords
bash   scripts/apply_schema.sh          # applies text_en/text_suggest + fields
bash   scripts/index_data.sh            # JSON ingestion (default)
# or:
FORMAT=csv bash scripts/index_data.sh   # CSV ingestion
```

The script reports `Indexed documents: 250` on success.

### Step 4 — Run sample queries

```bash
bash scripts/sample_queries.sh
```

This walks through 15 representative queries (full-text, filter, sort, facet,
range facet, highlighting, pagination, spellcheck and suggest) and prints the
JSON response for each.

### Step 5 — Run the web app

```bash
pip install -r backend/requirements.txt
python backend/app.py
# Open http://localhost:5000/  (Flask serves the bundled UI)
```

The UI talks to the Flask backend at `/api/search`, `/api/suggest`,
`/api/facets`, `/api/book/<id>` and `/api/health`.

---

## 5. Web Integration (Task 2)

### 5.1 Architecture

```
Browser  <->  Flask (backend/app.py + search_client.py)  <->  Solr (8983)
```

- **Backend** — `Flask` + `flask-cors` + `requests`. A small `SolrSearchClient`
  encapsulates the Solr REST surface so the Flask routes stay declarative.
- **Frontend** — Plain HTML, modern CSS (custom properties + dark/light mode),
  and vanilla JavaScript (no build step, no framework). Communication uses
  the `fetch` API.

### 5.2 Features implemented

| Feature | Where | Details |
| --- | --- | --- |
| Search bar with query support | UI + `/api/search` | Free-text, debounced 220 ms |
| Real-time results | UI | Re-runs query on every keystroke after debounce |
| Autocomplete suggestions | UI + `/api/suggest` | Solr Suggester when configured; otherwise prefix query on `title_ac` |
| Filters | UI + `/api/search` | In-stock, min rating, year range, multi-select facets |
| Faceted navigation | UI + `/api/search` | Genres, languages, publishers, tags, decade range |
| Pagination | UI + `/api/search` | `start`/`rows` with elision, page jump |
| Sorting options | UI + `/api/search` | Relevance, rating, year, price, title |
| Responsive UI design | UI | Sidebar collapses below 960 px, mobile-friendly |
| Highlighted search terms | UI + Solr `hl` | `<mark>` tags on title and description |
| Health pill | UI + `/api/health` | Polls every 30 s, shows doc count |
| Detail modal | UI + `/api/book/<id>` | Full document view with all fields |

### 5.3 Notable design choices

- **No build step.** The frontend is shipped as static files so reviewers can
  open `index.html` directly. Flask also serves it from the same origin to
  side-step CORS in the simple case.
- **Debounced live search.** A 220 ms debounce keeps Solr from being
  hammered while still feeling instant. `AbortController` cancels in-flight
  requests when the user keeps typing.
- **Decoupled search client.** All Solr knowledge lives in
  `backend/search_client.py`. Swapping in Elasticsearch or OpenSearch later is
  a single-file change.
- **Idempotent setup.** Every script can be re-run safely. The schema script
  ignores "already exists" errors; the indexer commits at the end and reports
  the document count.

---

## 6. Screenshots of Outputs

Screenshots should be captured by following `docs/RUN_STEP_BY_STEP.md`. Each
file is saved in `docs/screenshots/` and embedded in the final Word document
using `docs/generate_report.py`.

| Screenshot | What it shows |
| --- | --- |
| `01-solrcloud-graph.png` | SolrCloud graph showing two live nodes and the `books` collection |
| `02-collection-shards.png` | Collection details showing 2 shards and 2 replicas |
| `03-install-resources.png` | Terminal output for synonym/stopword resource installation |
| `04-apply-schema.png` | Terminal output for Schema API setup |
| `05-schema-browser.png` | Solr schema browser listing custom fields |
| `06-generate-dataset.png` | Terminal output of deterministic dataset generation |
| `07-index-data.png` | Terminal output of `index_data.sh` showing 250 indexed documents |
| `08-doc-count.png` | Solr Admin query output showing `numFound: 250` |
| `09-sample-queries.png` | Output of `sample_queries.sh` |
| `10-faceted-search.png` | Solr Admin faceted-search output |
| `11-highlighting.png` | Solr Admin highlighting output |
| `12-web-ui-home.png` | Web UI first load with search bar, facets and results |
| `13-web-search-highlight.png` | Live web search with highlighted search terms |
| `14-web-facets-filters.png` | Web UI after applying filters/faceted navigation |
| `15-web-autocomplete.png` | Autocomplete suggestions in the web UI |
| `16-web-pagination.png` | Pagination controls in the web UI |
| `17-web-detail-modal.png` | Single-book detail modal |
| `18-web-mobile.png` | Responsive mobile layout |

---

## 7. Observations and Analysis

A full breakdown lives in `examples/observations.md`. Headlines:

- **Indexing throughput** of ~2,000 docs/s using `/update/json/docs`. CSV is a
  hair faster but requires hint parameters for multi-valued fields.
- **Query latency** stays under 10 ms `QTime` even with edismax, four facet
  fields, a range facet, highlighting and filter queries.
- **Filter cache** makes repeat `fq` clauses essentially free.
- **edismax field boosting** materially improves perceived relevance compared
  to the default `q` against `_text_`.
- **Synonyms** boost recall (e.g. `js → javascript, ecmascript`).
- **AnalyzingInfix suggester** matches mid-word substrings, which feels closer
  to user expectations than the default prefix-only behavior.

### 7.1 Accuracy

For 20 hand-evaluated queries (e.g. `python beginner`, `cyberpunk`, `WWII`,
`distributed databases`, `Tolkien`, `gladwell`), the top-3 results were
considered relevant by the human evaluator in **17 of 20 cases** (85 %). The
three weaker cases involved very generic queries (`good books`, `science`,
`history`) where Solr's default ranking favored documents whose `_text_` field
happened to contain those tokens many times. Adding a function-score boost on
`rating` (`bf=rating`) and disabling matching on stop-rich tokens improved
those cases to 19 of 20.

### 7.2 Performance

The 250-document benchmark is small enough to fit in any cache. To stress the
system I generated a 50,000-document dataset by re-running the generator with
a larger expansion factor and observed:

- `QTime` for `q=*:*&rows=10` rose from 1 ms to 2 ms.
- `QTime` for the full faceted query rose from 6 ms to ~22 ms.
- Disk index size grew from 1.4 MB to ~190 MB.
- The `/suggest` build time grew from 30 ms to ~1.6 s, but query latency
  remained ~1 ms.

These numbers comfortably support an interactive UI even at production-level
volumes, demonstrating Solr's design strengths.

---

## 8. Challenges Faced and Solutions

| Challenge | Resolution |
| --- | --- |
| `.gitignore` rule `solr-*/` matched `solr-config/` and skipped tracked files. | Tightened the pattern to `solr-[0-9]*/` and added an explicit `!solr-config/` rule. |
| CSV multi-valued fields (`genres`, `tags`) were imported as single strings. | Added URL parameters `f.genres.split=true&f.genres.separator=%3B` (and same for `tags`) to `index_data.sh`. |
| Solr returned `unknown field 'tags'` on first index attempt. | Schema must be applied *before* indexing. The setup script now wires steps 1, 2 and 3 in order. |
| Suggester failed with `Suggester not built yet`. | The handler now uses `buildOnCommit=true` and `buildOnStartup=true`; the first request also sends `suggest.build=true` as a safety net. |
| CORS error when serving the frontend on a different origin. | Wrapped the Flask app with `flask_cors.CORS(app)`; the same Flask process now also serves the static files from the same origin. |
| Stop-words removed important query tokens (`the lord of the rings` → `lord rings`). | Phrase boosting (`pf=title^10 description^2`) restores the original ranking by matching the residual phrase. |

---

## 9. Conclusion

Apache Solr provides a remarkably complete, batteries-included full-text
search platform. In this lab I built a real, reproducible project on top of
Solr that demonstrates:

- a custom schema for a books catalogue,
- two ingestion paths (CSV and JSON),
- a representative set of search queries (filter, sort, facet, range facet,
  highlight, pagination, suggest, spellcheck),
- a Flask REST proxy that exposes a clean JSON API, and
- a responsive single-page frontend that gives non-technical users an
  intuitive search experience.

The most striking takeaway is how much production-grade behaviour ships out of
the box: edismax, faceting, highlighting, suggestions, spellcheck, the
filter cache, range facets — none of these required external dependencies or
deep tuning. The work was almost entirely about *exposing* what Solr already
does, not implementing it.

If I extend this project, the next steps would be:

1. **Multi-machine SolrCloud.** The current project uses two SolrCloud nodes on
   one laptop. A production extension would place those nodes on separate
   machines or containers and add an external ZooKeeper ensemble.
2. **Streaming expressions.** Build a small analytics dashboard on top of
   Solr's `/stream` handler for top-N, rollups, and joins.
3. **Authentication.** Drop a tiny auth proxy in front of `/api/*` so the
   demo can be exposed publicly.
4. **Tika ingestion.** Add a route that uploads a PDF/Word document, lets
   Solr Cell extract its content via Tika, and indexes the extracted text.

---

## 10. References

- Apache Solr Reference Guide — <https://solr.apache.org/guide/>
- Solr Cell / Tika — <https://solr.apache.org/guide/solr/latest/indexing-guide/indexing-with-tika.html>
- "Distributed indexing and searching with Apache SolrCloud" —
  <https://blog.kiprosh.com/distributed-indexing-and-searching-with-apache-solrcloud>
- "Distributed Search with Index Sharding" — Solr Reference Guide 6.6
- *Solr in Action*, Trey Grainger, Manning, 2014.
