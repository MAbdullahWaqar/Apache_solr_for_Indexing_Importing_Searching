#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# install_resources.sh
#
# Installs the project's synonyms.txt and stopwords.txt into the running
# Solr instance so that the `text_en` field type defined by apply_schema.sh
# can resolve them.
#
# Detects whether Solr is running in standalone or cloud mode:
#   * Cloud mode -> uses `bin/solr zk cp` to push the files into ZooKeeper
#                   and reloads the collection so analyzers re-read them.
#   * Standalone -> copies the files into the core's conf/ directory and
#                   reloads the core.
#
# Required env vars (with defaults):
#   SOLR_PORT        (default 8983)
#   CORE_NAME        (default books)            -- core or collection name
#   ZK_HOST          (default localhost:9983)   -- only used in cloud mode
# -----------------------------------------------------------------------------
set -euo pipefail

SOLR_PORT="${SOLR_PORT:-8983}"
CORE_NAME="${CORE_NAME:-books}"
ZK_HOST="${ZK_HOST:-localhost:9983}"

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
RES_DIR="${ROOT_DIR}/solr-config"
SYN_FILE="${RES_DIR}/synonyms.txt"
STOP_FILE="${RES_DIR}/stopwords.txt"
BASE="http://localhost:${SOLR_PORT}/solr"

if [ ! -f "${SYN_FILE}" ] || [ ! -f "${STOP_FILE}" ]; then
  echo "Error: missing ${SYN_FILE} or ${STOP_FILE}"
  exit 1
fi

# ---------------------------------------------------------------------------
# Detect mode
# ---------------------------------------------------------------------------
SYSTEM_INFO=$(curl -fsS "${BASE}/admin/info/system" 2>/dev/null || echo "")
if echo "${SYSTEM_INFO}" | grep -q '"mode":"solrcloud"'; then
  MODE="cloud"
elif echo "${SYSTEM_INFO}" | grep -q '"zkHost"'; then
  MODE="cloud"
else
  MODE="standalone"
fi

echo "Detected Solr mode: ${MODE}"

# ---------------------------------------------------------------------------
# Cloud mode: push files into ZooKeeper for the collection's configset
# ---------------------------------------------------------------------------
if [ "${MODE}" = "cloud" ]; then
  echo "Pushing resources into ZK at /configs/${CORE_NAME}/"
  solr zk cp "file:${SYN_FILE}"  "zk:/configs/${CORE_NAME}/synonyms.txt"  -z "${ZK_HOST}" || true
  solr zk cp "file:${STOP_FILE}" "zk:/configs/${CORE_NAME}/stopwords.txt" -z "${ZK_HOST}" || true

  echo "Reloading collection '${CORE_NAME}'..."
  curl -fsS "${BASE}/admin/collections?action=RELOAD&name=${CORE_NAME}&wt=json" \
    | python3 -m json.tool | head -20
  exit 0
fi

# ---------------------------------------------------------------------------
# Standalone mode: copy into the core's conf/ directory
# ---------------------------------------------------------------------------
# Ask Solr where the core's instance directory lives so we don't hard-code
# SOLR_HOME.
INSTANCE_DIR=$(curl -fsS "${BASE}/admin/cores?action=STATUS&core=${CORE_NAME}&wt=json" \
  | python3 -c '
import json, sys
d = json.load(sys.stdin)
core = d.get("status", {}).get(sys.argv[1], {})
print(core.get("instanceDir", ""))' "${CORE_NAME}")

if [ -z "${INSTANCE_DIR}" ] || [ ! -d "${INSTANCE_DIR}" ]; then
  echo "Could not determine instanceDir for core '${CORE_NAME}'."
  echo "Got: '${INSTANCE_DIR}'"
  echo "Make sure Solr is running and the core exists."
  exit 1
fi

CONF_DIR="${INSTANCE_DIR%/}/conf"
mkdir -p "${CONF_DIR}"

echo "Copying resources to ${CONF_DIR}"
cp "${SYN_FILE}"  "${CONF_DIR}/synonyms.txt"
cp "${STOP_FILE}" "${CONF_DIR}/stopwords.txt"

echo "Reloading core '${CORE_NAME}'..."
curl -fsS "${BASE}/admin/cores?action=RELOAD&core=${CORE_NAME}&wt=json" \
  | python3 -m json.tool | head -20
echo "Done."
