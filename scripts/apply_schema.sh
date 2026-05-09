#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# apply_schema.sh
#
# Pushes the project's field types and fields to a running Solr core
# (standalone) or collection (SolrCloud) via the Schema API.
#
# Idempotent: each "add" is allowed to fail with `|| true` so re-running on a
# core that already has the type/field is harmless.
#
# Field types created here:
#   * text_suggest -- Edge n-grams for autocomplete (title_ac)
#   * text_en      -- English text with stop filter, possessive filter, Porter
#                     stemmer; query time also applies SynonymGraphFilter.
#                     Resolves to synonyms.txt and stopwords.txt that
#                     install_resources.sh placed in the core's conf/ dir
#                     (or in ZK for SolrCloud).
#
# Required env vars (with defaults):
#   SOLR_PORT  - Solr port           (default 8983)
#   CORE_NAME  - Target core/coll.   (default books)
# -----------------------------------------------------------------------------
set -euo pipefail

SOLR_PORT="${SOLR_PORT:-8983}"
CORE_NAME="${CORE_NAME:-books}"
BASE="http://localhost:${SOLR_PORT}/solr/${CORE_NAME}"

post() {
  local payload="$1"
  curl -fsS -X POST -H 'Content-type: application/json' \
       --data-binary "${payload}" "${BASE}/schema" \
    | python3 -m json.tool || {
    echo "Schema API call failed for payload:"
    echo "${payload}"
    return 1
  }
}

# ---------------------------------------------------------------------------
# 1. Field type: text_suggest (edge-n-grams for autocomplete)
# ---------------------------------------------------------------------------
echo "[1/4] Adding field type 'text_suggest'..."
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

# ---------------------------------------------------------------------------
# 2. Field type: text_en (stopwords + Porter stemmer + synonyms at query time)
# ---------------------------------------------------------------------------
echo "[2/4] Adding field type 'text_en' (stopwords + stemming + synonyms)..."
post '{
  "add-field-type": [
    {
      "name": "text_en",
      "class": "solr.TextField",
      "positionIncrementGap": "100",
      "indexAnalyzer": {
        "tokenizer": {"class": "solr.StandardTokenizerFactory"},
        "filters": [
          {"class": "solr.StopFilterFactory", "ignoreCase": "true", "words": "stopwords.txt"},
          {"class": "solr.LowerCaseFilterFactory"},
          {"class": "solr.EnglishPossessiveFilterFactory"},
          {"class": "solr.PorterStemFilterFactory"}
        ]
      },
      "queryAnalyzer": {
        "tokenizer": {"class": "solr.StandardTokenizerFactory"},
        "filters": [
          {"class": "solr.StopFilterFactory", "ignoreCase": "true", "words": "stopwords.txt"},
          {"class": "solr.SynonymGraphFilterFactory", "synonyms": "synonyms.txt", "ignoreCase": "true", "expand": "true"},
          {"class": "solr.LowerCaseFilterFactory"},
          {"class": "solr.EnglishPossessiveFilterFactory"},
          {"class": "solr.PorterStemFilterFactory"}
        ]
      }
    }
  ]
}' || true

# ---------------------------------------------------------------------------
# 3. Fields
# ---------------------------------------------------------------------------
echo "[3/4] Adding fields..."
FIELDS_JSON=$(cat <<'EOF'
{
  "add-field": [
    {"name": "title",       "type": "text_en",      "indexed": true, "stored": true, "multiValued": false},
    {"name": "title_str",   "type": "string",       "indexed": true, "stored": true, "multiValued": false, "docValues": true},
    {"name": "title_ac",    "type": "text_suggest", "indexed": true, "stored": false, "multiValued": false},
    {"name": "author",      "type": "text_en",      "indexed": true, "stored": true, "multiValued": false},
    {"name": "author_str",  "type": "string",       "indexed": true, "stored": true, "multiValued": false, "docValues": true},
    {"name": "genres",      "type": "strings",      "indexed": true, "stored": true},
    {"name": "language",    "type": "string",       "indexed": true, "stored": true, "docValues": true},
    {"name": "year",        "type": "pint",         "indexed": true, "stored": true, "docValues": true},
    {"name": "pages",       "type": "pint",         "indexed": true, "stored": true, "docValues": true},
    {"name": "rating",      "type": "pfloat",       "indexed": true, "stored": true, "docValues": true},
    {"name": "price",       "type": "pfloat",       "indexed": true, "stored": true, "docValues": true},
    {"name": "in_stock",    "type": "boolean",      "indexed": true, "stored": true, "docValues": true},
    {"name": "stock_count", "type": "pint",         "indexed": true, "stored": true, "docValues": true},
    {"name": "publisher",   "type": "string",       "indexed": true, "stored": true, "docValues": true},
    {"name": "isbn",        "type": "string",       "indexed": true, "stored": true},
    {"name": "pub_date",    "type": "pdate",        "indexed": true, "stored": true, "docValues": true},
    {"name": "tags",        "type": "strings",      "indexed": true, "stored": true},
    {"name": "description", "type": "text_en",      "indexed": true, "stored": true, "multiValued": false}
  ]
}
EOF
)
post "${FIELDS_JSON}" || true

# ---------------------------------------------------------------------------
# 4. copyFields
# ---------------------------------------------------------------------------
echo "[4/4] Adding copyFields..."
post '{
  "add-copy-field": [
    {"source": "title",       "dest": ["_text_", "title_str", "title_ac"]},
    {"source": "author",      "dest": ["_text_", "author_str"]},
    {"source": "description", "dest": "_text_"},
    {"source": "genres",      "dest": "_text_"},
    {"source": "tags",        "dest": "_text_"}
  ]
}' || true

echo
echo "Schema applied successfully."
echo "Tip: run 'bash scripts/install_resources.sh' first time so that"
echo "     synonyms.txt and stopwords.txt are present on the server."
