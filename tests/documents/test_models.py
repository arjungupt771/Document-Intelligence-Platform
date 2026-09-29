from datetime import datetime
from uuid import uuid4

from app.documents.models import (
    Document,
    DocumentStatus,
    DocumentType,
)


def test_document_can_be_created():
    now = datetime.now()

    document = Document(
        id=uuid4(),
        filename="invoice.pdf",
        content_type="application/pdf",
        size_bytes=1024,
        document_type=DocumentType.UNKNOWN,
        status=DocumentStatus.UPLOADED,
        storage_path="storage/test.pdf",
        created_at=now,
        updated_at=now,
    )

    assert document.filename == "invoice.pdf"
    assert document.document_type == DocumentType.UNKNOWN
    assert document.status == DocumentStatus.UPLOADED