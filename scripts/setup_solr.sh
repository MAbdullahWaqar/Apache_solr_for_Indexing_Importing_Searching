#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# setup_solr.sh
#
# Convenience script that:
#   1. Verifies that Solr is on PATH (or accepts SOLR_HOME).
#   2. Starts Solr on the chosen port (default 8983).
#   3. Creates the "books" core if it doesn't already exist.
#   4. Calls scripts/apply_schema.sh to push the project schema.
#
# Usage:
#   bash scripts/setup_solr.sh
#   SOLR_PORT=8984 bash scripts/setup_solr.sh
# -----------------------------------------------------------------------------
set -euo pipefail

SOLR_PORT="${SOLR_PORT:-8983}"
CORE_NAME="${CORE_NAME:-books}"
SOLR_URL="http://localhost:${SOLR_PORT}"

if ! command -v solr >/dev/null 2>&1; then
  echo "Error: 'solr' not on PATH."
  echo "Install Apache Solr 9.x and ensure 'solr' is callable, e.g.:"
  echo "  brew install solr"
  echo "  or download from https://solr.apache.org/downloads.html"
  exit 1
fi

echo "[1/4] Starting Solr on port ${SOLR_PORT} (if not already running)..."
if ! curl -fsS "${SOLR_URL}/solr/admin/info/system" >/dev/null 2>&1; then
  solr start -p "${SOLR_PORT}"
else
  echo "      Solr already running on ${SOLR_PORT}."
fi

echo "[2/4] Creating core '${CORE_NAME}' (idempotent)..."
if curl -fsS "${SOLR_URL}/solr/admin/cores?action=STATUS&core=${CORE_NAME}" \
    | grep -q "\"name\":\"${CORE_NAME}\""; then
  echo "      Core '${CORE_NAME}' already exists, skipping."
else
  solr create -c "${CORE_NAME}" -p "${SOLR_PORT}"
fi

echo "[3/4] Installing synonyms.txt + stopwords.txt..."
SOLR_PORT="${SOLR_PORT}" CORE_NAME="${CORE_NAME}" \
  bash "$(dirname "$0")/install_resources.sh"

echo "[4/4] Applying project schema via Schema API..."
SOLR_PORT="${SOLR_PORT}" CORE_NAME="${CORE_NAME}" \
  bash "$(dirname "$0")/apply_schema.sh"

echo
echo "Done. Admin UI: ${SOLR_URL}/solr/#/${CORE_NAME}"
echo "Next: bash scripts/index_data.sh    # ingest the dataset"
