# Lab 13 Runbook — Run the Lab and Capture Screenshots

This guide tells you exactly how to run the project, verify each lab requirement,
and capture the screenshots needed for the Word report.

Recommended screenshot folder:

```bash
docs/screenshots/
```

Use the filenames shown below so `docs/generate_report.py` can embed them when
you regenerate the Word report.

---

## 0. Prerequisites

Install these before starting:

1. **Apache Solr 9.x**
   - macOS:

```bash
brew install solr
```

   - Windows: download Solr 9.x from <https://solr.apache.org/downloads.html>,
     extract it, and add `solr-X.Y.Z/bin` to `PATH`.

2. **Python 3.9+**

```bash
python3 --version
```

3. **Git**

```bash
git --version
```

---

## 1. Open the project

```bash
cd "/Users/muhammadabdullahwaqar/Desktop/PDC Lab/Apache_solr_for_Indexing_Importing_Searching"
```

Check files:

```bash
ls
```

Expected important folders:

```text
backend/  data/  docs/  examples/  frontend/  scripts/  solr-config/
```

---

## 2. Run real SolrCloud with shards

This is the recommended run mode for the lab because it satisfies the
prerequisite: **Create a cluster of servers (shards).**

The script starts:

- Node 1: `localhost:8983`
- Node 2: `localhost:7574`
- Embedded ZooKeeper: `localhost:9983`
- Collection: `books`
- Shards: `2`
- Replication factor: `2`

Run:

```bash
bash scripts/setup_solrcloud.sh
```

If successful, it prints cluster status JSON.

### Screenshot 01 — SolrCloud graph

Open:

```text
http://localhost:8983/solr/#/~cloud?view=graph
```

Capture and save as:

```text
docs/screenshots/01-solrcloud-graph.png
```

What the screenshot should show:

- SolrCloud mode
- Two live nodes
- `books` collection
- `shard1` and `shard2`
- replicas distributed across ports `8983` and `7574`

### Screenshot 02 — Collection/shards details

Open:

```text
http://localhost:8983/solr/#/~cloud
```

or:

```text
http://localhost:8983/solr/#/books
```

Capture and save as:

```text
docs/screenshots/02-collection-shards.png
```

What it should show:

- Collection name `books`
- 2 shards
- 2 replicas

---

## 3. Install synonyms and stopwords

The project uses custom query resources:

- `solr-config/synonyms.txt`
- `solr-config/stopwords.txt`

Push them into ZooKeeper for SolrCloud:

```bash
bash scripts/install_resources.sh
```

Expected output:

```text
Detected Solr mode: cloud
Pushing resources into ZK at /configs/books/
Reloading collection 'books'...
```

### Screenshot 03 — Resource installation terminal

Capture the terminal after this command and save as:

```text
docs/screenshots/03-install-resources.png
```

---

## 4. Apply schema

Apply all custom fields and analyzers:

```bash
bash scripts/apply_schema.sh
```

This creates:

- `text_en` with stopwords, stemming, and query-time synonyms
- `text_suggest` for autocomplete
- fields such as `title`, `author`, `genres`, `rating`, `price`, `pub_date`
- `copyField` rules into `_text_`, `title_str`, `title_ac`, and `author_str`

Expected output includes:

```text
[1/4] Adding field type 'text_suggest'...
[2/4] Adding field type 'text_en'...
[3/4] Adding fields...
[4/4] Adding copyFields...
Schema applied successfully.
```

### Screenshot 04 — Schema API terminal

Capture the terminal output and save as:

```text
docs/screenshots/04-apply-schema.png
```

### Screenshot 05 — Solr schema browser

Open:

```text
http://localhost:8983/solr/#/books/schema
```

Search for fields:

- `title`
- `genres`
- `rating`
- `title_ac`

Capture and save as:

```text
docs/screenshots/05-schema-browser.png
```

---

## 5. Generate the dataset

The dataset is already committed, but run the generator to prove reproducibility:

```bash
python3 scripts/generate_dataset.py
```

Expected output:

```text
Wrote 250 records
CSV : .../data/books.csv
JSON: .../data/books.json
```

### Screenshot 06 — Dataset generation

Capture the terminal and save as:

```text
docs/screenshots/06-generate-dataset.png
```

Optional verification:

```bash
wc -l data/books.csv
python3 -m json.tool data/books.json | head
```

---

## 6. Index data into SolrCloud

Index the JSON dataset:

```bash
bash scripts/index_data.sh
```

Expected output:

```text
Indexing .../data/books.json as JSON...
Indexed documents: 250
```

### Screenshot 07 — Indexing output

Capture and save as:

```text
docs/screenshots/07-index-data.png
```

### Screenshot 08 — Document count in Solr Admin

Open:

```text
http://localhost:8983/solr/#/books/query
```

Use:

```text
q = *:*
rows = 0
```

Click **Execute Query**.

Capture and save as:

```text
docs/screenshots/08-doc-count.png
```

It should show `numFound: 250`.

---

## 7. Run search-query demonstrations

Run the provided script:

```bash
bash scripts/sample_queries.sh
```

This demonstrates:

- Match all
- Full-text search
- Phrase search
- Field search
- Filtering
- Sorting
- Faceting
- Range faceting
- Highlighting
- Pagination
- Spellcheck
- Suggest/autocomplete
- JSON Facet API

### Screenshot 09 — Sample query script output

Capture a terminal section showing multiple query headings and JSON output:

```text
docs/screenshots/09-sample-queries.png
```

### Screenshot 10 — Faceted search in Solr Admin

Open:

```text
http://localhost:8983/solr/#/books/query
```

Use these parameters:

```text
q = *:*
facet = true
facet.field = genres
facet.field = language
rows = 0
```

Capture and save:

```text
docs/screenshots/10-faceted-search.png
```

### Screenshot 11 — Highlighting in Solr Admin

Use:

```text
q = algorithms
hl = true
hl.fl = title,description
rows = 5
```

Capture and save:

```text
docs/screenshots/11-highlighting.png
```

---

## 8. Run the Flask backend and web UI

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

Run the backend:

```bash
python backend/app.py
```

Expected output:

```text
Solr base : http://localhost:8983/solr/books
Flask API : http://0.0.0.0:5000
Open       http://localhost:5000/  for the bundled UI
```

Open:

```text
http://localhost:5000/
```

On macOS, port `5000` may already be used by AirPlay Receiver and may return
HTTP 403. If that happens, run Flask on port `5001`:

```bash
FLASK_PORT=5001 python backend/app.py
```

Then open:

```text
http://localhost:5001/
```

### Screenshot 12 — Web UI home

Capture initial page:

```text
docs/screenshots/12-web-ui-home.png
```

Should show:

- Search bar
- Solr health pill with 250 docs
- Facet sidebar
- Book cards

### Screenshot 13 — Live search with highlights

Search:

```text
distributed systems
```

Capture:

```text
docs/screenshots/13-web-search-highlight.png
```

Should show highlighted matches and filtered results.

### Screenshot 14 — Filters and facets

Apply:

- Genre: `Programming` or `Distributed Systems`
- Min rating: `4.0`
- Sort: `Rating ↓`

Capture:

```text
docs/screenshots/14-web-facets-filters.png
```

### Screenshot 15 — Autocomplete

Type:

```text
des
```

Pause before pressing Enter.

Capture:

```text
docs/screenshots/15-web-autocomplete.png
```

### Screenshot 16 — Pagination

Clear search, scroll bottom, show pagination.

Capture:

```text
docs/screenshots/16-web-pagination.png
```

### Screenshot 17 — Detail modal

Click any book card.

Capture:

```text
docs/screenshots/17-web-detail-modal.png
```

### Screenshot 18 — Responsive/mobile view

Open browser developer tools and set viewport to a mobile size, e.g.:

```text
390 x 844
```

Capture:

```text
docs/screenshots/18-web-mobile.png
```

---

## 9. Add screenshots to the Word report

After placing screenshots in `docs/screenshots/`, regenerate the Word document:

```bash
source .venv/bin/activate
python docs/generate_report.py
```

It writes:

```text
docs/Lab_13_Report.docx
```

Copy the final report to the parent lab folder:

```bash
cp docs/Lab_13_Report.docx "../Lab_13_Solution_Report.docx"
```

Open the Word document and verify:

- Screenshots appear in the appendix or screenshots section.
- GitHub link is present.
- SolrCloud/sharding is documented.
- Dataset/config/implementation/observations/challenges/conclusion exist.

---

## 10. Commit screenshots and final report

After screenshots are added:

```bash
git status
git add docs/screenshots/*.png docs/Lab_13_Report.docx ../Lab_13_Solution_Report.docx
git commit -m "docs: add lab screenshots and final Word report"
git push
```

If Git refuses to add `../Lab_13_Solution_Report.docx`, that is fine because it
is outside the repository. The committed copy inside the repo is:

```text
docs/Lab_13_Report.docx
```

---

## 11. LMS submission checklist

Submit these:

1. **Word report**
   - `Lab_13_Solution_Report.docx`, or
   - `Apache_solr_for_Indexing_Importing_Searching/docs/Lab_13_Report.docx`

2. **Code files**
   - Zip the full repo folder except `.venv/`, or submit the GitHub link.

3. **GitHub link**

```text
https://github.com/MAbdullahWaqar/Apache_solr_for_Indexing_Importing_Searching
```

---

## 12. Optional cleanup commands

Stop Solr nodes:

```bash
solr stop -p 8983
solr stop -p 7574
```

Delete the collection and rerun from scratch:

```bash
curl "http://localhost:8983/solr/admin/collections?action=DELETE&name=books"
bash scripts/setup_solrcloud.sh
bash scripts/install_resources.sh
bash scripts/apply_schema.sh
bash scripts/index_data.sh
```

