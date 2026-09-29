from pathlib import Path

from app.parsing.errors import CorruptedDocumentError
from app.parsing.pdf_parser import PDFParser
from app.parsing.docx_parser import DOCXParser


class DocumentContentVerifier:
    """Verifies that uploaded bytes match the claimed document type."""

    _PARSERS = {
        ".pdf": PDFParser(),
        ".docx": DOCXParser(),
    }

    def verify(self, path: Path, filename: str) -> None:
        extension = Path(filename).suffix.lower()

        parser = self._PARSERS.get(extension)
        if parser is None:
            raise ValueError(f"Unsupported document type: {extension}")

        try:
            
            parser.parse(
                path,
                document_id="content-verification",
                source_filename=filename,
            )
        except CorruptedDocumentError as exc:
            raise ValueError("Invalid document content") from exc