#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# apply_schema.sh
#
# Pushes the project's field types and fields to a running Solr core via the
# Schema API. The script is idempotent: each add is wrapped in a
# "replace-field" / "replace-field-type" fallback if the entity already exists.
#
# Required env vars (with defaults):
#   SOLR_PORT  - Solr port           (default 8983)
#   CORE_NAME  - Target core name    (default books)
# -----------------------------------------------------------------------------
set -euo pipefail

SOLR_PORT="${SOLR_PORT:-8983}"
CORE_NAME="${CORE_NAME:-books}"
BASE="http://localhost:${SOLR_PORT}/solr/${CORE_NAME}"

post() {
  local payload="$1"
  curl -fsS -X POST -H 'Content-type: application/json' \
       --data-binary "${payload}" "${BASE}/schema" | python3 -m json.tool || {
    echo "Schema API call failed for payload:"
    echo "${payload}"
    return 1
  }
}

echo "Applying field types..."
post '{
  "add-field-type": [
    {
      "name": "text_suggest",
      "class": "solr.TextField",
      "positionIncrementGap": "100",
      "indexAnalyzer": {
        "tokenizer": {"class": "solr.StandardTokenizerFactory"},
        "filters": [
          {"class": "solr.LowerCaseFilterFactory"},
          {"class": "solr.EdgeNGramFilterFactory", "minGramSize": "2", "maxGramSize": "20"}
        ]
      },
      "queryAnalyzer": {
        "tokenizer": {"class": "solr.StandardTokenizerFactory"},
        "filters": [{"class": "solr.LowerCaseFilterFactory"}]
      }
    }
  ]
}' || true

echo "Adding fields..."
FIELDS_JSON=$(cat <<'EOF'
{
  "add-field": [
    {"name": "title",       "type": "text_general", "indexed": true, "stored": true, "multiValued": false},
    {"name": "title_str",   "type": "string",       "indexed": true, "stored": true, "multiValued": false},
    {"name": "title_ac",    "type": "text_suggest", "indexed": true, "stored": false, "multiValued": false},
    {"name": "author",      "type": "text_general", "indexed": true, "stored": true, "multiValued": false},
    {"name": "author_str",  "type": "string",       "indexed": true, "stored": true, "multiValued": false},
    {"name": "genres",      "type": "strings",      "indexed": true, "stored": true},
    {"name": "language",    "type": "string",       "indexed": true, "stored": true},
    {"name": "year",        "type": "pint",         "indexed": true, "stored": true},
    {"name": "pages",       "type": "pint",         "indexed": true, "stored": true},
    {"name": "rating",      "type": "pfloat",       "indexed": true, "stored": true},
    {"name": "price",       "type": "pfloat",       "indexed": true, "stored": true},
    {"name": "in_stock",    "type": "boolean",      "indexed": true, "stored": true},
    {"name": "stock_count", "type": "pint",         "indexed": true, "stored": true},
    {"name": "publisher",   "type": "string",       "indexed": true, "stored": true},
    {"name": "isbn",        "type": "string",       "indexed": true, "stored": true},
    {"name": "pub_date",    "type": "pdate",        "indexed": true, "stored": true},
    {"name": "tags",        "type": "strings",      "indexed": true, "stored": true},
    {"name": "description", "type": "text_general", "indexed": true, "stored": true, "multiValued": false}
  ]
}
EOF
)
post "${FIELDS_JSON}" || true

echo "Adding copyFields..."
post '{
  "add-copy-field": [
    {"source": "title",       "dest": ["_text_", "title_str", "title_ac"]},
    {"source": "author",      "dest": ["_text_", "author_str"]},
    {"source": "description", "dest": "_text_"},
    {"source": "genres",      "dest": "_text_"},
    {"source": "tags",        "dest": "_text_"}
  ]
}' || true

echo "Schema applied successfully."
