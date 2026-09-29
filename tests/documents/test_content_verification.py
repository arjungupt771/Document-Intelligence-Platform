from io import BytesIO
from pathlib import Path

import pytest
from docx import Document as DocxDocument

from app.documents.content_verification import DocumentContentVerifier


def test_invalid_pdf_content_is_rejected(tmp_path: Path):
    path = tmp_path / "fake.pdf"
    path.write_bytes(b"this is not a real PDF")

    verifier = DocumentContentVerifier()

    with pytest.raises(ValueError, match="Invalid document content"):
        verifier.verify(path, "fake.pdf")


def test_valid_pdf_content_is_accepted(tmp_path: Path):
    path = tmp_path / "valid.pdf"

    import pymupdf

    document = pymupdf.open()
    page = document.new_page()
    page.insert_text((72, 72), "Valid PDF")
    document.save(path)
    document.close()

    DocumentContentVerifier().verify(path, "valid.pdf")


def test_invalid_docx_content_is_rejected(tmp_path: Path):
    path = tmp_path / "fake.docx"
    path.write_bytes(b"this is not a real DOCX package")

    verifier = DocumentContentVerifier()

    with pytest.raises(ValueError, match="Invalid document content"):
        verifier.verify(path, "fake.docx")


def test_valid_docx_content_is_accepted(tmp_path: Path):
    path = tmp_path / "valid.docx"

    document = DocxDocument()
    document.add_paragraph("Valid DOCX")
    document.save(path)

    DocumentContentVerifier().verify(path, "valid.docx")