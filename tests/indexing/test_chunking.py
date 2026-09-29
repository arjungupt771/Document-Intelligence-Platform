from app.indexing.chunking import chunk_document
from app.indexing.config import ChunkingSettings
from app.parsing.models import BlockType, DocumentMetadata, Page, ParsedDocument, Provenance, TextBlock


def _page(page_number: int, text: str) -> Page:
    provenance = Provenance(source_parser="test", page_number=page_number, block_index=0)
    return Page(
        page_number=page_number,
        width=None,
        height=None,
        text_blocks=[TextBlock(text=text, block_type=BlockType.TEXT, provenance=provenance)],
    )


def _document(pages_text: list[str]) -> ParsedDocument:
    return ParsedDocument(
        document_id="doc-1",
        source_filename="test.pdf",
        parser_name="test",
        metadata=DocumentMetadata(),
        pages=[_page(i + 1, text) for i, text in enumerate(pages_text)],
    )


def test_short_page_produces_single_chunk():
    document = _document(["short page text here"])
    chunks = chunk_document(document, ChunkingSettings(chunk_size=220, chunk_overlap=40))
    assert len(chunks) == 1
    assert chunks[0].page_number == 1


def test_long_page_splits_with_overlap():
    words = [f"word{i}" for i in range(500)]
    document = _document([" ".join(words)])
    settings = ChunkingSettings(chunk_size=200, chunk_overlap=50)

    chunks = chunk_document(document, settings)

    assert len(chunks) > 1
    first_tail = chunks[0].text.split()[-50:]
    second_head = chunks[1].text.split()[:50]
    assert first_tail == second_head


def test_empty_pages_are_skipped():
    document = _document(["", "   ", "real content"])
    chunks = chunk_document(document)
    assert len(chunks) == 1
    assert chunks[0].page_number == 3


def test_chunk_index_is_sequential_across_pages():
    document = _document(["page one text", "page two text"])
    chunks = chunk_document(document)
    assert [c.chunk_index for c in chunks] == list(range(len(chunks)))


def test_no_pages_produces_no_chunks():
    document = _document([])
    assert chunk_document(document) == []
