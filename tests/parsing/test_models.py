from app.parsing.models import (
    BlockType,
    DocumentMetadata,
    Page,
    ParsedDocument,
    Provenance,
    TextBlock,
)


def _text_block(text: str, page_number: int, index: int) -> TextBlock:
    return TextBlock(
        text=text,
        block_type=BlockType.TEXT,
        provenance=Provenance(
            source_parser="test",
            page_number=page_number,
            block_index=index,
        ),
    )


def test_page_text_joins_blocks_in_order():
    page = Page(
        page_number=1,
        width=612,
        height=792,
        text_blocks=[
            _text_block("Hello", 1, 0),
            _text_block("World", 1, 1),
        ],
    )

    assert page.text == "Hello\nWorld"


def test_parsed_document_aggregates_text_across_pages():
    page_one = Page(page_number=1, width=None, height=None, text_blocks=[_text_block("A", 1, 0)])
    page_two = Page(page_number=2, width=None, height=None, text_blocks=[_text_block("B", 2, 0)])

    document = ParsedDocument(
        document_id="doc-1",
        source_filename="file.pdf",
        parser_name="test",
        metadata=DocumentMetadata(page_count=2),
        pages=[page_one, page_two],
    )

    assert document.text == "A\n\nB"


def test_parsed_document_aggregates_tables_and_images_across_empty_pages():
    document = ParsedDocument(
        document_id="doc-1",
        source_filename="file.pdf",
        parser_name="test",
        metadata=DocumentMetadata(),
        pages=[],
    )

    assert document.tables == []
    assert document.images == []
