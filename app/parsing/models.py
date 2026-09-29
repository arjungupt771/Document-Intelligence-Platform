from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class BlockType(str, Enum):
    TEXT = "text"
    HEADING = "heading"
    TABLE = "table"
    IMAGE = "image"


@dataclass(frozen=True)
class BoundingBox:
    """Position of a block on a page, in the source format's coordinate space."""

    x0: float
    y0: float
    x1: float
    y1: float


@dataclass(frozen=True)
class Provenance:
    """
    Traces one extracted block back to where it came from in the source
    file, so downstream consumers (and humans debugging extraction) can
    answer "where did this text/table/image come from?".
    """

    source_parser: str
    """Name of the concrete parser/library that produced this block, e.g. 'pymupdf'."""

    page_number: Optional[int]
    """1-indexed page number. None for formats without a native page concept."""

    block_index: int
    """Position of this block within its page, in document order."""

    bbox: Optional[BoundingBox] = None
    """Layout position on the page, when the source format exposes one."""


@dataclass
class TextBlock:
    text: str
    block_type: BlockType
    provenance: Provenance


@dataclass
class TableCell:
    text: str
    row: int
    column: int
    row_span: int = 1
    column_span: int = 1


@dataclass
class TableBlock:
    rows: int
    columns: int
    cells: list[TableCell]
    provenance: Provenance


@dataclass
class ImageBlock:
    image_index: int
    width: Optional[int]
    height: Optional[int]
    format: Optional[str]
    provenance: Provenance
    data: Optional[bytes] = None


@dataclass
class Page:
    """One page of layout in the source document.

    For formats with no real pagination (e.g. .docx before layout/render),
    the whole document is represented as a single Page.
    """

    page_number: int
    width: Optional[float]
    height: Optional[float]
    text_blocks: list[TextBlock] = field(default_factory=list)
    tables: list[TableBlock] = field(default_factory=list)
    images: list[ImageBlock] = field(default_factory=list)

    @property
    def text(self) -> str:
        return "\n".join(block.text for block in self.text_blocks)


@dataclass
class DocumentMetadata:
    title: Optional[str] = None
    author: Optional[str] = None
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None
    page_count: int = 0
    source_content_type: str = ""
    extra: dict = field(default_factory=dict)


@dataclass
class ParsedDocument:
    """
    Canonical, parser-agnostic representation of a parsed document.
    Everything downstream of Phase 2 (classification, extraction, ...)
    depends only on this shape -- never on Docling/PyMuPDF/python-docx
    types directly.
    """

    document_id: str
    source_filename: str
    parser_name: str
    metadata: DocumentMetadata
    pages: list[Page] = field(default_factory=list)

    @property
    def text(self) -> str:
        return "\n\n".join(page.text for page in self.pages)

    @property
    def tables(self) -> list[TableBlock]:
        return [table for page in self.pages for table in page.tables]

    @property
    def images(self) -> list[ImageBlock]:
        return [image for page in self.pages for image in page.images]
