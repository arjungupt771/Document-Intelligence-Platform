from sqlalchemy.orm import Session

from app.storage.repository import DriftAlertRepository, DriftResultRepository


def build_drift_dashboard(session: Session) -> dict:
    results = DriftResultRepository(session).list_latest(limit=200)
    alerts = DriftAlertRepository(session).list_unacknowledged()

    latest_by_key: dict[tuple, dict] = {}
    for result in results:
        key = (result.dimension.value, result.key)
        if key in latest_by_key:
            continue  # results are already ordered newest-first, so the first hit per key is the latest
        latest_by_key[key] = {
            "dimension": result.dimension.value,
            "key": result.key,
            "score": round(result.score, 4),
            "severity": result.severity.value,
            "detected_at": result.detected_at.isoformat(),
        }

    return {
        "latest_drift": list(latest_by_key.values()),
        "unacknowledged_alerts": len(alerts),
    }