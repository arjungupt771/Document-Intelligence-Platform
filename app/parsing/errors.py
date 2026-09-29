class ParserError(Exception):
    """Base class for all document-parsing errors."""


class UnsupportedFileTypeError(ParserError):
    """No parser is registered for the file's extension."""

    def __init__(self, extension: str):
        self.extension = extension
        super().__init__(f"No parser registered for file type '{extension}'")


class CorruptedDocumentError(ParserError):
    """The file could not be opened or parsed by its underlying library."""

    def __init__(self, filename: str, reason: str):
        self.filename = filename
        self.reason = reason
        super().__init__(f"Failed to parse '{filename}': {reason}")


class EmptyDocumentError(ParserError):
    """Parsing succeeded but produced no extractable content."""

    def __init__(self, filename: str):
        self.filename = filename
        super().__init__(f"Document '{filename}' contains no extractable content")
