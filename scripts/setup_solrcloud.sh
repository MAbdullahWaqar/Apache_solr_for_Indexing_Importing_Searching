#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# setup_solrcloud.sh
#
# Stands up a real SolrCloud cluster on a single host:
#   * Node 1 on port 8983 (with embedded ZooKeeper on port 9983)
#   * Node 2 on port 7574 (joins the same ensemble)
#   * Collection "books" with 2 shards x 2 replicas (replicationFactor=2)
#
# After this script finishes you will have one logical collection backed by
# four Solr cores (2 shards x 2 replicas) distributed across the two nodes.
# This satisfies the lab prerequisite of "Create a cluster of servers (shards)"
# without needing a multi-machine deployment.
#
# Usage:
#   bash scripts/setup_solrcloud.sh
#   COLLECTION=books NUM_SHARDS=2 REPLICATION_FACTOR=2 bash scripts/setup_solrcloud.sh
#
# After it completes you can run:
#   bash scripts/install_resources.sh   # push synonyms/stopwords into ZK
#   bash scripts/apply_schema.sh        # add custom field types & fields
#   bash scripts/index_data.sh          # ingest data/books.json
# -----------------------------------------------------------------------------
set -euo pipefail

PORT_1="${PORT_1:-8983}"
PORT_2="${PORT_2:-7574}"
ZK_PORT="${ZK_PORT:-9983}"
COLLECTION="${COLLECTION:-books}"
NUM_SHARDS="${NUM_SHARDS:-2}"
REPLICATION_FACTOR="${REPLICATION_FACTOR:-2}"
ZK_HOST="${ZK_HOST:-localhost:${ZK_PORT}}"

if ! command -v solr >/dev/null 2>&1; then
  echo "Error: 'solr' not on PATH."
  echo "Install Apache Solr 9.x (e.g. brew install solr) and re-run."
  exit 1
fi

echo "================================================================="
echo " SolrCloud setup"
echo "   Node 1 port      : ${PORT_1}"
echo "   Node 2 port      : ${PORT_2}"
echo "   Embedded ZK port : ${ZK_PORT}"
echo "   Collection       : ${COLLECTION}"
echo "   Shards x Replicas: ${NUM_SHARDS} x ${REPLICATION_FACTOR}"
echo "================================================================="

# ---------------------------------------------------------------------------
# 1. Start node 1 in cloud mode (this also brings up the embedded ZooKeeper).
#    Solr 10 starts in SolrCloud mode by default; older Solr 9 releases used
#    `-c`. The modern syntax below works for Solr 10 and avoids the deprecated
#    `-c` flag.
# ---------------------------------------------------------------------------
echo "[1/4] Starting node 1 in cloud mode on port ${PORT_1}..."
if ! curl -fsS "http://localhost:${PORT_1}/solr/admin/info/system" >/dev/null 2>&1; then
  solr start -p "${PORT_1}"
else
  echo "      Node 1 already running on ${PORT_1}."
fi

# Give the embedded ZooKeeper a moment to bind
sleep 2

# ---------------------------------------------------------------------------
# 2. Start node 2 in cloud mode and join the existing ensemble
# ---------------------------------------------------------------------------
echo "[2/4] Starting node 2 on port ${PORT_2}, joining ZK ${ZK_HOST}..."
if ! curl -fsS "http://localhost:${PORT_2}/solr/admin/info/system" >/dev/null 2>&1; then
  solr start -p "${PORT_2}" -z "${ZK_HOST}"
else
  echo "      Node 2 already running on ${PORT_2}."
fi

# ---------------------------------------------------------------------------
# 3. Create the collection (idempotent)
# ---------------------------------------------------------------------------
echo "[3/4] Creating collection '${COLLECTION}' (idempotent)..."
LIVE_NODES=$(curl -fsS "http://localhost:${PORT_1}/solr/admin/collections?action=clusterstatus&wt=json" \
  || echo "")

if echo "${LIVE_NODES}" | grep -q "\"${COLLECTION}\""; then
  echo "      Collection '${COLLECTION}' already exists, skipping."
else
  solr create \
    -c "${COLLECTION}" \
    -sh "${NUM_SHARDS}" \
    -rf "${REPLICATION_FACTOR}" \
    -s "http://localhost:${PORT_1}"
fi

# ---------------------------------------------------------------------------
# 4. Print cluster status
# ---------------------------------------------------------------------------
echo "[4/4] Cluster status:"
curl -fsS "http://localhost:${PORT_1}/solr/admin/collections?action=clusterstatus&wt=json" \
  | python3 -m json.tool \
  | sed -n '1,60p'

echo
echo "Done."
echo "  Admin UI (node 1) : http://localhost:${PORT_1}/solr/#/~cloud?view=graph"
echo "  Admin UI (node 2) : http://localhost:${PORT_2}/solr/#/~cloud?view=graph"
echo
echo "Next steps:"
echo "  bash scripts/install_resources.sh   # push synonyms/stopwords to ZK"
echo "  bash scripts/apply_schema.sh        # add field types & fields"
echo "  bash scripts/index_data.sh          # ingest dataset"
