#!/usr/bin/env bash
set -euo pipefail

PREVIOUS_IMAGE_FILE=".previous_image"

if [ ! -f "$PREVIOUS_IMAGE_FILE" ]; then
    echo "No recorded previous image found. Check deploy history manually." >&2
    exit 1
fi

PREVIOUS_IMAGE=$(tr -d '[:space:]' < "$PREVIOUS_IMAGE_FILE")

if [ -z "$PREVIOUS_IMAGE" ]; then
    echo "Recorded previous image is empty. Check deploy history manually." >&2
    exit 1
fi

echo "Rolling back to image: $PREVIOUS_IMAGE"

export IMAGE_REGISTRY="${PREVIOUS_IMAGE%/document-intelligence:*}"
export IMAGE_TAG="${PREVIOUS_IMAGE##*:}"

docker compose -f docker-compose.yml -f docker-compose.prod.yml pull api
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --no-deps --wait api

python scripts/smoke_test.py && {
    echo "Rollback verified healthy."
} || {
    echo "Rollback smoke test also failed -- this needs a human now." >&2
    exit 1
}