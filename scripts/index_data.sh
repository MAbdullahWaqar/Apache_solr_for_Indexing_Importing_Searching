#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# index_data.sh
#
# Indexes data/books.json (preferred) or data/books.csv into the configured
# Solr core via the standard /update handlers. Commits at the end.
#
# Env vars:
#   SOLR_PORT  - Solr port           (default 8983)
#   CORE_NAME  - Target core name    (default books)
#   FORMAT     - "json" or "csv"     (default json)
# -----------------------------------------------------------------------------
set -euo pipefail

SOLR_PORT="${SOLR_PORT:-8983}"
CORE_NAME="${CORE_NAME:-books}"
FORMAT="${FORMAT:-json}"
BASE="http://localhost:${SOLR_PORT}/solr/${CORE_NAME}"

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
DATA_DIR="${ROOT_DIR}/data"

case "${FORMAT}" in
  json)
    FILE="${DATA_DIR}/books.json"
    if [ ! -f "${FILE}" ]; then
      echo "Missing ${FILE}; run scripts/generate_dataset.py first."
      exit 1
    fi
    echo "Indexing ${FILE} as JSON..."
    curl -fsS -X POST \
      -H 'Content-type: application/json' \
      --data-binary "@${FILE}" \
      "${BASE}/update/json/docs?commit=true" | python3 -m json.tool
    ;;

  csv)
    FILE="${DATA_DIR}/books.csv"
    if [ ! -f "${FILE}" ]; then
      echo "Missing ${FILE}; run scripts/generate_dataset.py first."
      exit 1
    fi
    echo "Indexing ${FILE} as CSV..."
    # Note: multi-valued fields (genres, tags) use ';' as the separator.
    curl -fsS -X POST \
      -H 'Content-type: application/csv' \
      --data-binary "@${FILE}" \
      "${BASE}/update?commit=true&f.genres.split=true&f.genres.separator=%3B&f.tags.split=true&f.tags.separator=%3B" \
      | python3 -m json.tool
    ;;

  *)
    echo "Unknown FORMAT='${FORMAT}'. Expected 'json' or 'csv'."
    exit 1
    ;;
esac

echo
echo "Verifying document count..."
curl -fsS "${BASE}/select?q=*:*&rows=0" | python3 -c '
import json, sys
d = json.load(sys.stdin)
print("Indexed documents:", d["response"]["numFound"])
'
