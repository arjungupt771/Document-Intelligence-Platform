# from datetime import datetime
# from pathlib import Path
# from uuid import uuid4
# from app.storage.database import session_scope
# from app.storage.repository import DocumentRepository, compute_content_hash
# from fastapi import APIRouter, File, HTTPException, UploadFile, status
# from app.documents.content_verification import DocumentContentVerifier
# from app.documents.models import Document, DocumentStatus, DocumentType
# from app.documents.storage import DocumentStorage
# from app.documents.validation import validate_file, MAX_FILE_SIZE


# router = APIRouter(prefix="/documents", tags=["documents"])

# STORAGE_ROOT = Path("storage/documents")
# storage = DocumentStorage(STORAGE_ROOT)
# content_verifier = DocumentContentVerifier()

# @router.post("/", status_code=status.HTTP_201_CREATED)
# async def upload_document(file: UploadFile = File(...)):
#     filename = file.filename or "unknown"

#     extension_validation = validate_file(
#         filename=filename,
#         size_bytes=1,
#     )

#     if (not extension_validation.valid 
#         and extension_validation.reason == "Unsupported file type"):
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=extension_validation.reason,
#         )

#     document_id = uuid4()

#     try:
#         size_bytes = storage.write_stream(
#             document_id=document_id,
#             stream=file.file,
#             max_size=MAX_FILE_SIZE,
#         )

#         validation = validate_file(
#             filename=filename,
#             size_bytes=size_bytes,
#         )

#         if not validation.valid:
#             storage.delete(document_id)

#             status_code = (
#                 status.HTTP_413_CONTENT_TOO_LARGE
#                 if size_bytes > MAX_FILE_SIZE
#                 else status.HTTP_400_BAD_REQUEST
#             )

#             raise HTTPException(
#                 status_code=status_code,
#                 detail=validation.reason,
#             )

#         try:
#             content_verifier.verify(
#                 storage.create_temp_path(document_id),
#                 filename,
#             )
#         except ValueError as exc:
#             storage.delete(document_id)
#             raise HTTPException(
#                 status_code = 400,
#                 detail = str(exc)
#             ) from exc

#         storage_path = storage.finalize(document_id)

#     except ValueError as exc:
#         storage.delete(document_id)

#         raise HTTPException(
#             status_code=status.HTTP_413_CONTENT_TOO_LARGE,
#             detail=str(exc),
#         ) from exc

#     now = datetime.now()

#     document = Document(
#         id=document_id,
#         filename=filename,
#         content_type=file.content_type or "application/octet-stream",
#         size_bytes=size_bytes,
#         document_type=DocumentType.UNKNOWN,
#         status=DocumentStatus.UPLOADED,
#         storage_path=str(storage_path),
#         created_at=now,
#         updated_at=now,
#     )
#     content_hash = compute_content_hash(storage_path)

#     with session_scope() as db:
#         DocumentRepository(db).create(
#             document=document,
#             content_hash=content_hash,
#         )

#     return {
#         "document_id": str(document.id),
#         "filename": document.filename,
#         "status": document.status.value,
#     }\


import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session
from app.documents.processing import DocumentProcessingService
from app.documents.content_verification import DocumentContentVerifier
from app.documents.models import Document, DocumentStatus, DocumentType
from app.documents.storage import DocumentStorage
from app.documents.validation import MAX_FILE_SIZE, validate_file
from app.storage.database import get_db
from app.storage.repository import DocumentRepository, DuplicateDocumentError, compute_content_hash

router = APIRouter(prefix="/documents", tags=["documents"])

STORAGE_ROOT = Path("storage/documents")
storage = DocumentStorage(STORAGE_ROOT)
content_verifier = DocumentContentVerifier()


def _document_response(document: Document) -> dict:
    return {
        "document_id": str(document.id),
        "filename": document.filename,
        "content_type": document.content_type,
        "size_bytes": document.size_bytes,
        "document_type": document.document_type.value,
        "status": document.status.value,
        "created_at": document.created_at.isoformat(),
        "updated_at": document.updated_at.isoformat(),
    }


@router.post("/", status_code=status.HTTP_201_CREATED)
async def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db)):
    filename = file.filename or "unknown"

    extension_validation = validate_file(filename=filename, size_bytes=1)
    if not extension_validation.valid and extension_validation.reason == "Unsupported file type":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=extension_validation.reason)

    document_id = uuid.uuid4()

    try:
        size_bytes = storage.write_stream(document_id=document_id, stream=file.file, max_size=MAX_FILE_SIZE)

        validation = validate_file(filename=filename, size_bytes=size_bytes)
        if not validation.valid:
            storage.delete(document_id)
            status_code = (
                status.HTTP_413_CONTENT_TOO_LARGE
                if size_bytes > MAX_FILE_SIZE
                else status.HTTP_400_BAD_REQUEST
            )
            raise HTTPException(status_code=status_code, detail=validation.reason)

        temp_path = storage.create_temp_path(document_id)
        try:
            content_verifier.verify(temp_path, filename)
        except ValueError as exc:
            storage.delete(document_id)
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        content_hash = compute_content_hash(temp_path)
        storage_path = storage.finalize(document_id)

    except ValueError as exc:
        storage.delete(document_id)
        raise HTTPException(status_code=status.HTTP_413_CONTENT_TOO_LARGE, detail=str(exc)) from exc

    now = datetime.now()
    document = Document(
        id=document_id,
        filename=filename,
        content_type=file.content_type or "application/octet-stream",
        size_bytes=size_bytes,
        document_type=DocumentType.UNKNOWN,
        status=DocumentStatus.UPLOADED,
        storage_path=str(storage_path),
        created_at=now,
        updated_at=now,
    )

    try:
        saved = DocumentRepository(db).create(document, content_hash)
        db.commit()
    except DuplicateDocumentError as exc:
        db.rollback()
        storage.delete(document_id)  # don't keep an orphaned file for content we already have
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"This file's content was already uploaded as document {exc.existing_document_id}.",
        ) from exc

    return _document_response(saved)


@router.get("/")
def list_documents(
    document_type: DocumentType | None = None,
    status_filter: DocumentStatus | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    documents = DocumentRepository(db).list(
        status=status_filter, document_type=document_type, limit=limit, offset=offset
    )
    return {"items": [_document_response(d) for d in documents], "limit": limit, "offset": offset}


@router.get("/{document_id}")
def get_document(document_id: uuid.UUID, db: Session = Depends(get_db)):
    document = DocumentRepository(db).get(document_id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return _document_response(document)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(document_id: uuid.UUID, db: Session = Depends(get_db)):
    deleted = DocumentRepository(db).delete(document_id)
    db.commit()
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    storage.delete(document_id)
    return None

@router.post("/{document_id}/process")
def process_document(
    document_id: uuid.UUID,
):
    service = DocumentProcessingService()

    try:
        return service.process(document_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc