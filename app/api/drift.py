import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.documents.models import DocumentType
from app.drift.dashboard import build_drift_dashboard
from app.drift.factory import build_drift_service
from app.drift.models import DriftResult
from app.storage.database import get_db
from app.storage.repository import DriftAlertRepository, DriftResultRepository

router = APIRouter(prefix="/drift", tags=["drift"])


class DriftResultResponse(BaseModel):
    dimension: str
    key: str
    score: float
    severity: str
    baseline_summary: dict
    current_summary: dict


def _to_response(result: DriftResult) -> DriftResultResponse:
    return DriftResultResponse(
        dimension=result.dimension.value,
        key=result.key,
        score=round(result.score, 4),
        severity=result.severity.value,
        baseline_summary=result.baseline_summary,
        current_summary=result.current_summary,
    )


class BaselineRequest(BaseModel):
    document_type: DocumentType


@router.post("/baseline")
def establish_baseline(request: BaselineRequest, db: Session = Depends(get_db)):
    service = build_drift_service(db)
    snapshot_id = service.establish_baseline(request.document_type)
    db.commit()
    return {"snapshot_id": snapshot_id, "established": snapshot_id is not None}


class DriftCheckRequest(BaseModel):
    document_type: DocumentType
    current_hit_rate: float | None = None
    current_mrr: float | None = None


@router.post("/check", response_model=list[DriftResultResponse])
def check_drift(request: DriftCheckRequest, db: Session = Depends(get_db)):
    service = build_drift_service(db)
    results = service.check_drift(
        request.document_type,
        current_hit_rate=request.current_hit_rate,
        current_mrr=request.current_mrr,
    )
    db.commit()
    return [_to_response(r) for r in results]


@router.get("/results", response_model=list[DriftResultResponse])
def list_drift_results(limit: int = 50, db: Session = Depends(get_db)):
    results = DriftResultRepository(db).list_latest(limit=limit)
    return [_to_response(r) for r in results]


@router.get("/alerts")
def list_alerts(db: Session = Depends(get_db)):
    alerts = DriftAlertRepository(db).list_unacknowledged()
    return [
        {
            "id": str(alert.id),
            "message": alert.message,
            "created_at": alert.created_at.isoformat(),
            "drift_result_id": str(alert.drift_result_id),
        }
        for alert in alerts
    ]


@router.post("/alerts/{alert_id}/acknowledge")
def acknowledge_alert(alert_id: uuid.UUID, db: Session = Depends(get_db)):
    DriftAlertRepository(db).acknowledge(alert_id)
    db.commit()
    return {"acknowledged": True}


@router.get("/dashboard")
def drift_dashboard(db: Session = Depends(get_db)):
    return build_drift_dashboard(db)