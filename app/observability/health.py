from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional

from qdrant_client import QdrantClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.indexing.collections import get_qdrant_client
from app.indexing.config import QdrantSettings

HEALTH_CHECK_TIMEOUT_SECONDS = 3  # short and separate from the app's normal query timeout


@dataclass(frozen=True)
class ComponentHealth:
    name: str
    healthy: bool
    detail: Optional[str] = None
    latency_ms: Optional[float] = None


def check_database(session: Session) -> ComponentHealth:
    start = time.perf_counter()
    try:
        session.execute(text("SELECT 1"))
        return ComponentHealth(name="database", healthy=True, latency_ms=_elapsed_ms(start))
    except Exception:
        return ComponentHealth(
            name="database", healthy=False, detail="Database health check failed",
            latency_ms=_elapsed_ms(start),
        )


def check_qdrant(
    client: Optional[QdrantClient] = None, settings: Optional[QdrantSettings] = None
) -> ComponentHealth:
    settings = settings or QdrantSettings.from_env()
    start = time.perf_counter()
    try:
        # Deliberately short-lived client for the probe itself so a slow/hanging
        # Qdrant can't stall the readiness endpoint for the full app timeout.
        probe_client = client or get_qdrant_client_with_timeout(settings, HEALTH_CHECK_TIMEOUT_SECONDS)
        probe_client.get_collections()
        return ComponentHealth(name="qdrant", healthy=True, latency_ms=_elapsed_ms(start))
    except Exception:
        return ComponentHealth(
            name="qdrant", healthy=False, detail="Qdrant health check failed",
            latency_ms=_elapsed_ms(start),
        )


def get_qdrant_client_with_timeout(settings: QdrantSettings, timeout_seconds: int) -> QdrantClient:
    return QdrantClient(url=settings.url, api_key=settings.api_key, timeout=timeout_seconds)


def _elapsed_ms(start: float) -> float:
    return round((time.perf_counter() - start) * 1000, 1)