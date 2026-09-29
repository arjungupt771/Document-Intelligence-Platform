import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.documents.models import Document, DocumentStatus, DocumentType
from app.drift.service import DriftMonitoringService
from app.extraction.base import ExtractionResult
from app.extraction.schemas import InvoiceSchema
from app.storage.database import Base
from app.storage.repository import (
    BaselineSnapshotRepository,
    DocumentRepository,
    DriftAlertRepository,
    DriftResultRepository,
    ExtractionRepository,
)


@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    try:
        yield db
    finally:
        db.close()
        engine.dispose()


def _seed_invoices(session, totals):
    documents = DocumentRepository(session)
    extractions = ExtractionRepository(session)
    now = datetime.now(timezone.utc)
    for total in totals:
        document = documents.create(
            Document(
                id=uuid.uuid4(), filename="i.pdf", content_type="application/pdf", size_bytes=1,
                document_type=DocumentType.INVOICE, status=DocumentStatus.READY, storage_path="x",
                created_at=now, updated_at=now,
            ),
            content_hash=str(uuid.uuid4()),
        )
        extractions.save_result(
            document.id, DocumentType.INVOICE,
            ExtractionResult(data=InvoiceSchema(vendor="Acme", total=total), confidence=0.9),
        )
    session.commit()


def _service(session) -> DriftMonitoringService:
    return DriftMonitoringService(
        document_repository=DocumentRepository(session),
        extraction_repository=ExtractionRepository(session),
        baseline_repository=BaselineSnapshotRepository(session),
        drift_result_repository=DriftResultRepository(session),
        drift_alert_repository=DriftAlertRepository(session),
    )


class TestDriftMonitoringService:
    def test_check_drift_without_baseline_returns_empty(self, session):
        _seed_invoices(session, ["100", "200"])
        assert _service(session).check_drift(DocumentType.INVOICE) == []

    def test_establish_then_check_drift_flags_shifted_totals(self, session):
        _seed_invoices(session, ["100", "120", "110", "130", "105", "115"])
        service = _service(session)

        snapshot_id = service.establish_baseline(DocumentType.INVOICE)
        session.commit()
        assert snapshot_id is not None

        _seed_invoices(session, ["9000", "9500", "10000", "8800", "9200"])

        results = service.check_drift(DocumentType.INVOICE)
        session.commit()

        numeric_results = [r for r in results if r.dimension.value == "numeric_value" and r.key == "total"]
        assert numeric_results
        assert numeric_results[0].severity.value != "none"

        alerts = DriftAlertRepository(session).list_unacknowledged()
        assert len(alerts) >= 1