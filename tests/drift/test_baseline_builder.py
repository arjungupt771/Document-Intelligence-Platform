import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.documents.models import Document, DocumentStatus, DocumentType
from app.drift.baseline_builder import BaselineSnapshotBuilder
from app.extraction.base import ExtractionResult
from app.extraction.schemas import InvoiceSchema
from app.storage.database import Base
from app.storage.repository import DocumentRepository, ExtractionRepository


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


class TestBaselineSnapshotBuilder:
    def test_returns_none_without_data(self, session):
        builder = BaselineSnapshotBuilder(DocumentRepository(session), ExtractionRepository(session))
        assert builder.build(DocumentType.INVOICE) is None

    def test_builds_snapshot_from_seeded_extractions(self, session):
        _seed_invoices(session, ["100", "200", "150", "300", "250", "175"])

        builder = BaselineSnapshotBuilder(DocumentRepository(session), ExtractionRepository(session))
        snapshot = builder.build(DocumentType.INVOICE)

        assert snapshot is not None
        assert snapshot.sample_size == 6
        assert "vendor" in snapshot.field_presence_rates
        assert "total" in snapshot.numeric_field_bins
        assert snapshot.mean_extraction_confidence == pytest.approx(0.9)