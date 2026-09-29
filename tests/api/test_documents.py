from io import BytesIO
import pymupdf
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine

from app.documents.validation import MAX_FILE_SIZE
from app.main import app
from pathlib import Path
from docx import Document as DocxDocument
import app.api.documents as documents_api
from app.documents.storage import DocumentStorage
from app.storage.database import Base, get_engine, get_session_factory, get_db



client = TestClient(app,
                    headers={"Authorization": "Bearer test-secret"},
                    raise_server_exceptions=True,)


@pytest.fixture(autouse=True)
def isolated_document_environment(tmp_path, monkeypatch):
    database_path = tmp_path.parent / f"{tmp_path.name}-db.sqlite"
    database_url = f"sqlite:///{database_path}"

    monkeypatch.setenv("DATABASE_URL", database_url)

    get_session_factory.cache_clear()
    get_engine.cache_clear()

    engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    engine.dispose()

    test_storage = DocumentStorage(tmp_path / "documents")
    monkeypatch.setattr(documents_api, "storage", test_storage)

    yield

    get_session_factory.cache_clear()
    get_engine.cache_clear()

def test_upload_document_successfully():
    document = pymupdf.open()
    page = document.new_page()
    page.insert_text((72, 72), "Valid PDF")
    
    buffer = BytesIO()
    document.save(buffer)
    document.close()
    buffer.seek(0)

    response = client.post(
        "/documents/",
        files={
            "file": (
                "invoice.pdf",
                buffer,
                "application/pdf",
            )
        },
    )

    assert response.status_code == 201

def test_upload_rejects_unsupported_file_type():
    response = client.post(
        "/documents/",
        files={
            "file": (
                "malware.exe",
                BytesIO(b"fake executable"),
                "application/octet-stream",
            )
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Unsupported file type"


def test_upload_rejects_oversized_file():
    oversized_content = b"x" * (MAX_FILE_SIZE + 1)

    response = client.post(
        "/documents/",
        files={
            "file": (
                "large.pdf",
                BytesIO(oversized_content),
                "application/pdf",
            )
        },
    )

    assert response.status_code == 413
    assert (
        response.json()["detail"]
        == "File size exceeds maximum allowed size"
    )

def test_upload_rejects_empty_file():
    response = client.post(
        "/documents/",
        files={
            "file": (
                "empty.pdf",
                BytesIO(b""),
                "application/pdf",
            )
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "File is empty"


def test_oversized_upload_leaves_no_partial_file(tmp_path, monkeypatch):
    test_storage = DocumentStorage(tmp_path)

    monkeypatch.setattr(
        documents_api,
        "storage",
        test_storage,
    )

    oversized_content = b"x" * (MAX_FILE_SIZE + 1)

    response = client.post(
        "/documents/",
        files={
            "file": (
                "large.pdf",
                BytesIO(oversized_content),
                "application/pdf",
            )
        },
    )

    assert response.status_code == 413

    assert list(Path(tmp_path).iterdir()) == []

def test_upload_stream_failure_leaves_no_partial_file(tmp_path, monkeypatch):
    test_storage = DocumentStorage(tmp_path)

    monkeypatch.setattr(
        documents_api,
        "storage",
        test_storage,
    )

    class FailingStream:
        def read(self, _chunk_size):
            raise OSError("simulated upload failure")

    document_id = __import__("uuid").uuid4()

    try:
        test_storage.write_stream(
            document_id=document_id,
            stream=FailingStream(),
            max_size=MAX_FILE_SIZE,
        )
    except OSError as exc:
        assert str(exc) == "simulated upload failure"

    assert list(Path(tmp_path).iterdir()) == []

def test_upload_rejects_invalid_pdf_content(tmp_path, monkeypatch):
    test_storage = DocumentStorage(tmp_path)

    monkeypatch.setattr(
        documents_api,
        "storage",
        test_storage,
    )

    response = client.post(
        "/documents/",
        files={
            "file": (
                "fake.pdf",
                BytesIO(b"this is not a real PDF"),
                "application/pdf",
            )
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid document content"
    assert list(Path(tmp_path).iterdir()) == []


def test_upload_accepts_valid_docx_content(tmp_path, monkeypatch):
    test_storage = DocumentStorage(tmp_path)

    monkeypatch.setattr(
        documents_api,
        "storage",
        test_storage,
    )

    document = DocxDocument()
    document.add_paragraph("Valid document content")

    buffer = BytesIO()
    document.save(buffer)
    buffer.seek(0)

    response = client.post(
        "/documents/",
        files={
            "file": (
                "valid.docx",
                buffer,
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )

    assert response.status_code == 201
    assert response.json()["filename"] == "valid.docx"