from pathlib import Path
from typing import Optional

from app.parsing.base import Parser
from app.parsing.docx_parser import DOCXParser
from app.parsing.errors import UnsupportedFileTypeError
from app.parsing.pdf_parser import PDFParser


class ParserFactory:
    """Resolves the right Parser adapter for a file, by extension.

    This is the single place that knows which concrete parser handles
    which file type. Callers ask for a parser by filename; they never
    import PDFParser/DOCXParser (or Docling/PyMuPDF) directly.
    """

    def __init__(self, parsers: Optional[list[Parser]] = None):
        self._parsers_by_extension: dict[str, Parser] = {}
        for parser in parsers if parsers is not None else self._default_parsers():
            self.register(parser)

    def register(self, parser: Parser) -> None:
        for extension in parser.supported_extensions:
            self._parsers_by_extension[extension.lower()] = parser

    def get_parser(self, filename: str) -> Parser:
        extension = Path(filename).suffix.lower()
        parser = self._parsers_by_extension.get(extension)

        if parser is None:
            raise UnsupportedFileTypeError(extension)

        return parser

    @staticmethod
    def _default_parsers() -> list[Parser]:
        return [PDFParser(), DOCXParser()]


default_parser_factory = ParserFactory()
