from pathlib import Path

import pymupdf

from app.parsing.base import Parser
from app.parsing.errors import CorruptedDocumentError, EmptyDocumentError
from app.parsing.models import (
    BlockType,
    BoundingBox,
    DocumentMetadata,
    ImageBlock,
    Page,
    ParsedDocument,
    Provenance,
    TableBlock,
    TableCell,
    TextBlock,
)

PARSER_NAME = "pymupdf"


class PDFParser(Parser):
    """Adapter from PyMuPDF (pymupdf) documents to ParsedDocument."""

    supported_extensions = frozenset({".pdf"})

    def parse(
        self,
        path: Path,
        *,
        document_id: str,
        source_filename: str,
    ) -> ParsedDocument:
        try:
            document = pymupdf.open(path)
        except Exception as exc:
            raise CorruptedDocumentError(source_filename, str(exc)) from exc

        try:
            pages = [
                self._parse_page(document, page_index)
                for page_index in range(document.page_count)
            ]
            metadata = self._build_metadata(document)
        except Exception as exc:
            raise CorruptedDocumentError(source_filename, str(exc)) from exc
        finally:
            document.close()

        parsed_document = ParsedDocument(
            document_id=document_id,
            source_filename=source_filename,
            parser_name=PARSER_NAME,
            metadata=metadata,
            pages=pages,
        )

        if not parsed_document.text.strip() and not parsed_document.tables and not parsed_document.images:
            raise EmptyDocumentError(source_filename)

        return parsed_document

    def _parse_page(self, document: "pymupdf.Document", page_index: int) -> Page:
        pdf_page = document[page_index]
        page_number = page_index + 1

        table_bboxes = self._table_bboxes(pdf_page)
        text_blocks = self._extract_text_blocks(pdf_page, page_number, table_bboxes)
        tables = self._extract_tables(pdf_page, page_number, start_index=len(text_blocks))
        images = self._extract_images(pdf_page, page_number)

        return Page(
            page_number=page_number,
            width=pdf_page.rect.width,
            height=pdf_page.rect.height,
            text_blocks=text_blocks,
            tables=tables,
            images=images,
        )

    def _extract_text_blocks(
        self,
        pdf_page: "pymupdf.Page",
        page_number: int,
        table_bboxes: list[tuple[float, float, float, float]],
    ) -> list[TextBlock]:
        raw_blocks = pdf_page.get_text("blocks")

        text_blocks: list[TextBlock] = []
        for raw_block in sorted(raw_blocks, key=lambda block: (round(block[1], 1), block[0])):
            x0, y0, x1, y1, text, *_ = raw_block
            text = text.strip()

            if not text:
                continue

            text_blocks.append(
                TextBlock(
                    text=text,
                    block_type=BlockType.TEXT,
                    provenance=Provenance(
                        source_parser=PARSER_NAME,
                        page_number=page_number,
                        block_index=len(text_blocks),
                        bbox=BoundingBox(x0, y0, x1, y1),
                    ),
                )
            )

        return text_blocks

    def _extract_tables(
        self,
        pdf_page: "pymupdf.Page",
        page_number: int,
        start_index: int,
    ) -> list[TableBlock]:
        tables: list[TableBlock] = []

        for offset, found_table in enumerate(self._find_tables(pdf_page)):
            rows = found_table.extract()
            row_count = len(rows)
            column_count = len(rows[0]) if rows else 0

            cells = [
                TableCell(text=(cell or "").strip(), row=row_index, column=column_index)
                for row_index, row in enumerate(rows)
                for column_index, cell in enumerate(row)
            ]

            tables.append(
                TableBlock(
                    rows=row_count,
                    columns=column_count,
                    cells=cells,
                    provenance=Provenance(
                        source_parser=PARSER_NAME,
                        page_number=page_number,
                        block_index=start_index + offset,
                        bbox=BoundingBox(*found_table.bbox),
                    ),
                )
            )

        return tables

    def _extract_images(self, pdf_page: "pymupdf.Page", page_number: int) -> list[ImageBlock]:
        images: list[ImageBlock] = []

        for image_index, image_info in enumerate(pdf_page.get_images(full=True)):
            width = image_info[2] or None
            height = image_info[3] or None

            images.append(
                ImageBlock(
                    image_index=image_index,
                    width=width,
                    height=height,
                    format=None,
                    provenance=Provenance(
                        source_parser=PARSER_NAME,
                        page_number=page_number,
                        block_index=image_index,
                    ),
                )
            )

        return images

    @staticmethod
    def _find_tables(pdf_page: "pymupdf.Page") -> list:
        finder = getattr(pdf_page, "find_tables", None)
        if finder is None:
            return []
        try:
            return list(finder().tables)
        except Exception:
            # Table detection is best-effort: a failure here should not
            # prevent text extraction from succeeding.
            return []

    @staticmethod
    def _table_bboxes(pdf_page: "pymupdf.Page") -> list[tuple[float, float, float, float]]:
        return [tuple(table.bbox) for table in PDFParser._find_tables(pdf_page)]

    @staticmethod
    def _is_inside_a_table(
        bbox: tuple[float, float, float, float],
        table_bboxes: list[tuple[float, float, float, float]],
    ) -> bool:
        x0, y0, x1, y1 = bbox
        for tx0, ty0, tx1, ty1 in table_bboxes:
            if x0 >= tx0 - 1 and y0 >= ty0 - 1 and x1 <= tx1 + 1 and y1 <= ty1 + 1:
                return True
        return False

    @staticmethod
    def _build_metadata(document: "pymupdf.Document") -> DocumentMetadata:
        info = document.metadata or {}
        return DocumentMetadata(
            title=info.get("title") or None,
            author=info.get("author") or None,
            page_count=document.page_count,
            source_content_type="application/pdf",
            extra={key: value for key, value in info.items() if value},
        )
