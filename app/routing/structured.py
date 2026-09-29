from __future__ import annotations

import uuid

from app.storage.repository import DocumentRepository, ExtractionRepository


class StructuredQueryService:
    def __init__(
        self,
        document_repository: DocumentRepository,
        extraction_repository: ExtractionRepository,
    ):
        self._documents = document_repository
        self._extractions = extraction_repository

    def get_document(self, document_id: uuid.UUID):
        return self._documents.get(document_id)

    def get_latest_extraction(self, document_id: uuid.UUID):
        return self._extractions.get_latest_for_document(document_id)