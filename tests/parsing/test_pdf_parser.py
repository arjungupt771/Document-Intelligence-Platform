import pymupdf
import pytest

from app.parsing.errors import CorruptedDocumentError, EmptyDocumentError
from app.parsing.pdf_parser import PDFParser


def _make_pdf(tmp_path, pages_text: list[str], filename: str = "sample.pdf"):
    document = pymupdf.open()

    for text in pages_text:
        page = document.new_page()
        y = 72
        for line in text.splitlines():
            page.insert_text((72, y), line)
            y += 20

    path = tmp_path / filename
    document.save(path)
    document.close()
    return path


def test_parses_text_and_document_metadata(tmp_path):
    path = _make_pdf(tmp_path, ["Invoice #123\nTotal: $50.00"])

    parsed = PDFParser().parse(path, document_id="doc-1", source_filename="sample.pdf")

    assert parsed.parser_name == "pymupdf"
    assert parsed.document_id == "doc-1"
    assert parsed.source_filename == "sample.pdf"
    assert parsed.metadata.page_count == 1
    assert parsed.metadata.source_content_type == "application/pdf"

    assert len(parsed.pages) == 1
    assert "Invoice #123" in parsed.pages[0].text
    assert "Total: $50.00" in parsed.pages[0].text


def test_text_blocks_carry_page_level_provenance(tmp_path):
    path = _make_pdf(tmp_path, ["Line one"])

    parsed = PDFParser().parse(path, document_id="doc-1", source_filename="sample.pdf")

    block = parsed.pages[0].text_blocks[0]
    assert block.provenance.source_parser == "pymupdf"
    assert block.provenance.page_number == 1
    assert block.provenance.block_index == 0
    assert block.provenance.bbox is not None


def test_multi_page_pdf_is_parsed_page_by_page(tmp_path):
    path = _make_pdf(tmp_path, ["Page one", "Page two"], filename="multi.pdf")

    parsed = PDFParser().parse(path, document_id="doc-1", source_filename="multi.pdf")

    assert parsed.metadata.page_count == 2
    assert [page.page_number for page in parsed.pages] == [1, 2]
    assert "Page one" in parsed.pages[0].text
    assert "Page one" not in parsed.pages[1].text
    assert "Page two" in parsed.pages[1].text


def test_corrupted_pdf_raises_corrupted_document_error(tmp_path):
    path = tmp_path / "bad.pdf"
    path.write_bytes(b"this is not a real pdf file")

    with pytest.raises(CorruptedDocumentError):
        PDFParser().parse(path, document_id="doc-1", source_filename="bad.pdf")


def test_blank_pdf_raises_empty_document_error(tmp_path):
    document = pymupdf.open()
    document.new_page()
    path = tmp_path / "blank.pdf"
    document.save(path)
    document.close()

    with pytest.raises(EmptyDocumentError):
        PDFParser().parse(path, document_id="doc-1", source_filename="blank.pdf")
