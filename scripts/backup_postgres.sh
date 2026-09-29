#!/usr/bin/env bash
set -euo pipefail

TIMESTAMP=$(date -u +%Y%m%dT%H%M%SZ)
BACKUP_DIR="${BACKUP_DIR:-/opt/backups/postgres}"
mkdir -p "$BACKUP_DIR"

docker compose exec -T postgres pg_dump -U "${POSTGRES_USER}" "${POSTGRES_DB}" \
    | gzip > "${BACKUP_DIR}/document_intelligence_${TIMESTAMP}.sql.gz"

# Retain 14 days, prune older -- adjust to your compliance requirements.
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +14 -delete

echo "Backup written: ${BACKUP_DIR}/document_intelligence_${TIMESTAMP}.sql.gz"