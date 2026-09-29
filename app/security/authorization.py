from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.storage.database import get_db
from app.storage.repository import DocumentRepository


def require_document_access(
    document_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Authorize access to an application-owned document.

    Authorization is currently resource-existence based because the
    application does not yet have users, tenants, or ownership metadata.
    """
    document = DocumentRepository(db).get(document_id)

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    return document


def require_documents_access(
    document_id_a: UUID,
    document_id_b: UUID,
    db: Session = Depends(get_db),
):
    repository = DocumentRepository(db)

    document_a = repository.get(document_id_a)
    if document_a is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    document_b = repository.get(document_id_b)
    if document_b is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    return document_a, document_b