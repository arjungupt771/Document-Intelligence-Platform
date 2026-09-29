from fastapi import APIRouter, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.observability.dashboard import build_dashboard_snapshot

router = APIRouter(tags=["metrics"])


@router.get("/metrics")
def prometheus_metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@router.get("/metrics/summary")
def metrics_summary():
    return build_dashboard_snapshot()