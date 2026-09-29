import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.analyst.service import AnalystService
from app.documents.models import Document, DocumentStatus, DocumentType
from app.extraction.base import ExtractionResult
from app.extraction.schemas import InvoiceSchema
from app.storage.database import Base
from app.storage.repository import DocumentRepository, ExtractionRepository, InsightRepository


@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        engine.dispose()


def _seed_invoice(session, total="150.00", subtotal="100.00", tax="0"):
    now = datetime.now(timezone.utc)
    documents = DocumentRepository(session)
    extractions = ExtractionRepository(session)

    document = documents.create(
        Document(
            id=uuid.uuid4(),
            filename="invoice.pdf",
            content_type="application/pdf",
            size_bytes=10,
            document_type=DocumentType.INVOICE,
            status=DocumentStatus.READY,
            storage_path="x",
            created_at=now,
            updated_at=now,
        ),
        content_hash=str(uuid.uuid4()),
    )

    result = ExtractionResult(
        data=InvoiceSchema(
            vendor="Acme",
            invoice_number="INV-1",
            total=total,
            subtotal=subtotal,
            tax=tax,
            currency="USD",
            line_items=[{"description": "A", "total": "90.00"}],
        ),
        confidence=0.9,
    )
    extractions.save_result(document.id, DocumentType.INVOICE, result)
    session.commit()
    return document


class TestAnalystService:
    def test_analyze_document_persists_insights(self, session):
        document = _seed_invoice(session, total="150.00", subtotal="100.00", tax="0")

        service = AnalystService(
            document_repository=DocumentRepository(session),
            extraction_repository=ExtractionRepository(session),
            insight_repository=InsightRepository(session),
        )

        report = service.analyze_document(document.id)
        session.commit()

        assert any(i.title == "Line items do not sum to subtotal" for i in report.insights)
        stored = InsightRepository(session).list_for_document(document.id)
        assert len(stored) == len(report.insights)

    def test_analyze_document_without_extraction_returns_empty_report(self, session):
        now = datetime.now(timezone.utc)
        document = DocumentRepository(session).create(
            Document(
                id=uuid.uuid4(),
                filename="x.pdf",
                content_type="application/pdf",
                size_bytes=10,
                document_type=DocumentType.INVOICE,
                status=DocumentStatus.UPLOADED,
                storage_path="x",
                created_at=now,
                updated_at=now,
            ),
            content_hash=str(uuid.uuid4()),
        )
        session.commit()

        service = AnalystService(
            document_repository=DocumentRepository(session),
            extraction_repository=ExtractionRepository(session),
            insight_repository=InsightRepository(session),
        )

        report = service.analyze_document(document.id)

        assert report.insights == []