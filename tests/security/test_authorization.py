import uuid
from unittest.mock import Mock

from fastapi import HTTPException

from app.security.authorization import (
    require_document_access,
    require_documents_access,
)


def test_document_access_is_rejected_when_document_does_not_exist():
    session = Mock()
    session.get.return_value = None

    document_id = uuid.uuid4()

    try:
        require_document_access(document_id=document_id, db=session)
    except HTTPException as exc:
        assert exc.status_code == 404
        assert exc.detail == "Document not found"
    else:
        raise AssertionError("Expected document access to be rejected")


def test_document_access_is_allowed_for_existing_document():
    session = Mock()

    document_id = uuid.uuid4()

    orm_document = Mock()
    orm_document.id = document_id
    orm_document.filename = "invoice.pdf"
    orm_document.content_type = "application/pdf"
    orm_document.size_bytes = 1024
    orm_document.document_type.value = "invoice"
    orm_document.status.value = "uploaded"
    orm_document.storage_path = "storage/documents/test/original"
    orm_document.created_at = None
    orm_document.updated_at = None

    session.get.return_value = orm_document

    result = require_document_access(
        document_id=document_id,
        db=session,
    )

    assert result.id == document_id
    assert result.filename == "invoice.pdf"

def test_documents_access_is_rejected_when_first_document_does_not_exist():
    session = Mock()

    first_document_id = uuid.uuid4()
    second_document_id = uuid.uuid4()

    session.get.return_value = None

    try:
        require_documents_access(
            document_id_a=first_document_id,
            document_id_b=second_document_id,
            db=session,
        )
    except HTTPException as exc:
        assert exc.status_code == 404
        assert exc.detail == "Document not found"
    else:
        raise AssertionError("Expected first document access to be rejected")


def test_documents_access_is_rejected_when_second_document_does_not_exist():
    session = Mock()

    first_document_id = uuid.uuid4()
    second_document_id = uuid.uuid4()

    first_document = Mock()
    first_document.id = first_document_id
    first_document.filename = "invoice.pdf"
    first_document.content_type = "application/pdf"
    first_document.size_bytes = 1024
    first_document.document_type.value = "invoice"
    first_document.status.value = "uploaded"
    first_document.storage_path = "storage/documents/test/original"
    first_document.created_at = None
    first_document.updated_at = None

    session.get.side_effect = [first_document, None]

    try:
        require_documents_access(
            document_id_a=first_document_id,
            document_id_b=second_document_id,
            db=session,
        )
    except HTTPException as exc:
        assert exc.status_code == 404
        assert exc.detail == "Document not found"
    else:
        raise AssertionError("Expected second document access to be rejected")