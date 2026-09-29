import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends
from app.security.authorization import (
    require_document_access,
    require_documents_access,
)
from app.analyst.factory import build_analyst_service
from app.analyst.models import Insight
from app.documents.models import DocumentType
from app.storage.database import get_db

router = APIRouter(prefix="/analyst", tags=["analyst"])
from app.analyst.models import InsightType, Severity
from app.storage.repository import InsightRepository



class InsightEvidenceResponse(BaseModel):
    document_id: str
    document_type: str
    text: str
    field_path: str | None = None
    page_number: int | None = None
    extraction_id: str | None = None


class InsightResponse(BaseModel):
    id: str
    type: str
    severity: str
    title: str
    description: str
    narrative: str | None
    confidence: float
    priority_score: float | None
    document_ids: list[str]
    evidence: list[InsightEvidenceResponse]


def _to_response(insight: Insight) -> InsightResponse:
    return InsightResponse(
        id=str(insight.id),
        type=insight.type.value,
        severity=insight.severity.value,
        title=insight.title,
        description=insight.description,
        narrative=insight.narrative,
        confidence=insight.confidence,
        priority_score=insight.priority_score,
        document_ids=insight.document_ids,
        evidence=[
            InsightEvidenceResponse(
                document_id=e.document_id,
                document_type=e.document_type,
                text=e.text,
                field_path=e.field_path,
                page_number=e.page_number,
                extraction_id=e.extraction_id,
            )
            for e in insight.evidence
        ],
    )


@router.post(
    "/documents/{document_id}/analyze",
    response_model=list[InsightResponse],
)
def analyze_document(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
    _document=Depends(require_document_access),
):
    service = build_analyst_service(db)
    report = service.analyze_document(document_id)
    db.commit()
    return [_to_response(insight) for insight in report.insights]


@router.get(
    "/documents/{document_id}/insights",
    response_model=list[InsightResponse],
)
def get_document_insights(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
    _document=Depends(require_document_access),
):
    service = build_analyst_service(db)
    insights = service.list_insights_for_document(document_id)
    return [_to_response(insight) for insight in insights]


class CompareRequest(BaseModel):
    document_id_a: uuid.UUID
    document_id_b: uuid.UUID


@router.post("/compare", response_model=list[InsightResponse])
def compare_documents(
    request: CompareRequest,
    db: Session = Depends(get_db),
):
    require_documents_access(
        document_id_a=request.document_id_a,
        document_id_b=request.document_id_b,
        db=db,
    )

    service = build_analyst_service(db)
    insights = service.compare_documents(
        request.document_id_a,
        request.document_id_b,
    )
    db.commit()
    return [_to_response(insight) for insight in insights]


class TrendRequest(BaseModel):
    document_type: DocumentType


@router.post("/trend", response_model=list[InsightResponse])
def analyze_trend(request: TrendRequest, db: Session = Depends(get_db)):
    service = build_analyst_service(db)
    insights = service.analyze_trend(request.document_type)
    db.commit()
    return [_to_response(insight) for insight in insights]


@router.get("/insights", response_model=list[InsightResponse])
def list_insights(
    severity: Severity | None = None,
    insight_type: InsightType | None = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    insights = InsightRepository(db).list(
        severity=severity, insight_type=insight_type, limit=limit, offset=offset
    )
    return [_to_response(i) for i in insights]