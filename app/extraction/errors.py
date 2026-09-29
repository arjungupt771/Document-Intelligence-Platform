from app.documents.models import DocumentType


class ExtractionError(Exception):
    """Base class for all extraction errors."""


class UnsupportedDocumentTypeError(ExtractionError):
    """No extractor is registered for this document type (e.g. UNKNOWN)."""

    def __init__(self, document_type: DocumentType):
        self.document_type = document_type
        super().__init__(f"No extractor registered for document type '{document_type.value}'")