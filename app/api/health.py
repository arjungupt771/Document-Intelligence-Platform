from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.observability.health import check_database, check_qdrant
from app.storage.database import get_db

router = APIRouter(tags=["health"])

DEGRADED_LATENCY_MS = 1000


@router.get("/health/live")
def liveness():
    return {"status": "alive"}


@router.get("/health/ready")
def readiness(response: Response, db: Session = Depends(get_db)):
    checks = [check_database(db), check_qdrant()]
    unhealthy = [c for c in checks if not c.healthy]
    degraded = [c for c in checks if c.healthy and (c.latency_ms or 0) > DEGRADED_LATENCY_MS]

    if unhealthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        overall = "not_ready"
    elif degraded:
        response.status_code = status.HTTP_200_OK
        overall = "degraded"
    else:
        overall = "ready"

    return {
        "status": overall,
        "checks": [
            {"name": c.name, "healthy": c.healthy, "detail": c.detail, "latency_ms": c.latency_ms}
            for c in checks
        ],
    }