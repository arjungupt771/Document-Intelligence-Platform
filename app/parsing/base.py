from abc import ABC, abstractmethod
from pathlib import Path

from app.parsing.models import ParsedDocument


class Parser(ABC):
    """
    Adapter interface between a specific parsing library (PyMuPDF,
    python-docx, Docling, ...) and our canonical ParsedDocument schema.

        Docling/PyMuPDF
               |
               v
        Parser Adapter (this interface)
               |
               v
        ParsedDocument

    Nothing outside app/parsing should import a parsing library directly.
    Everything else in the system depends only on ParsedDocument, so the
    underlying parsing technology can be swapped out later by writing a
    new adapter, without touching any caller.
    """

    supported_extensions: frozenset[str] = frozenset()
    """File extensions (lowercase, with leading dot) this parser can handle."""

    @abstractmethod
    def parse(
        self,
        path: Path,
        *,
        document_id: str,
        source_filename: str,
    ) -> ParsedDocument:
        """Parse the file at `path` into a ParsedDocument.

        Args:
            path: filesystem path to the file to parse.
            document_id: id of the Document this file belongs to (Phase 1).
            source_filename: original filename, for error messages and
                provenance -- not necessarily the same as `path.name`.

        Raises:
            CorruptedDocumentError: the file can't be opened or parsed.
            EmptyDocumentError: parsing succeeded but yielded no content.
        """
        raise NotImplementedError
