#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/opt/backups/qdrant}"
mkdir -p "$BACKUP_DIR"
TIMESTAMP=$(date -u +%Y%m%dT%H%M%SZ)

COLLECTION="${QDRANT_COLLECTION:-document_chunks}"
SNAPSHOT=$(curl -s -X POST "http://localhost:6333/collections/${COLLECTION}/snapshots" \
    -H "api-key: ${QDRANT_API_KEY}" | python3 -c "import sys,json; print(json.load(sys.stdin)['result']['name'])")

docker cp "$(docker compose ps -q qdrant):/qdrant/storage/snapshots/${COLLECTION}/${SNAPSHOT}" \
    "${BACKUP_DIR}/${COLLECTION}_${TIMESTAMP}.snapshot"

echo "Qdrant snapshot written: ${BACKUP_DIR}/${COLLECTION}_${TIMESTAMP}.snapshot"