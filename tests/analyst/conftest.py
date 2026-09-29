import uuid
from datetime import datetime, timezone

from app.documents.models import Document, DocumentStatus, DocumentType
from app.storage.models import DocumentTypeEnum, ExtractionORM, ExtractionStatusEnum


def make_document(document_type: DocumentType = DocumentType.INVOICE, **overrides) -> Document:
    now = datetime.now(timezone.utc)
    defaults = dict(
        id=uuid.uuid4(),
        filename="doc.pdf",
        content_type="application/pdf",
        size_bytes=100,
        document_type=document_type,
        status=DocumentStatus.READY,
        storage_path="storage/documents/x/original",
        created_at=now,
        updated_at=now,
    )
    defaults.update(overrides)
    return Document(**defaults)


def make_extraction(
    data: dict,
    document_type: DocumentType = DocumentType.INVOICE,
    confidence: float = 0.9,
    field_confidence: dict | None = None,
    document_id: uuid.UUID | None = None,
) -> ExtractionORM:
    return ExtractionORM(
        id=uuid.uuid4(),
        document_id=document_id or uuid.uuid4(),
        document_type=DocumentTypeEnum(document_type.value),
        status=ExtractionStatusEnum.COMPLETED,
        data=data,
        confidence=confidence,
        field_confidence=field_confidence or {},
        created_at=datetime.now(timezone.utc),
    )