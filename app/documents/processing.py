from pathlib import Path
from uuid import UUID

from app.classification.rule_based import RuleBasedClassifier
from app.documents.models import DocumentStatus
from app.extraction.pipeline import ExtractionPipeline
from app.indexing.collections import ensure_collection, get_qdrant_client
from app.indexing.config import QdrantSettings
from app.indexing.embeddings import get_embedding_model
from app.indexing.indexer import DocumentIndexer
from app.parsing.factory import default_parser_factory
from app.storage.database import session_scope
from app.storage.repository import DocumentRepository, ExtractionRepository


class DocumentProcessingService:
    """Orchestrates parsing, classification, extraction, indexing, and persistence."""

    def __init__(self):
        # Built once per service instance, not per document -- the Qdrant
        # client and embedding model are safe to reuse across calls.
        self._qdrant_settings = QdrantSettings.from_env()
        self._qdrant_client = get_qdrant_client(self._qdrant_settings)
        ensure_collection(self._qdrant_client, self._qdrant_settings)
        self._indexer = DocumentIndexer(
            client=self._qdrant_client,
            embedding_model=get_embedding_model(),
            settings=self._qdrant_settings,
        )

    def process(self, document_id: UUID):
        with session_scope() as db:
            documents = DocumentRepository(db)
            extractions = ExtractionRepository(db)

            document = documents.get(document_id)

            if document is None:
                raise ValueError(f"Document {document_id} not found")

            if document.status == DocumentStatus.PROCESSING:
                raise ValueError(f"Document {document_id} is already being processed")

            documents.update_status(document_id, DocumentStatus.PROCESSING)

            try:
                parser = default_parser_factory.get_parser(document.filename)
                parsed_document = parser.parse(
                    Path(document.storage_path),
                    document_id=str(document.id),
                    source_filename=document.filename,
                )

                pipeline = ExtractionPipeline(classifier=RuleBasedClassifier())
                result = pipeline.run(parsed_document)

                documents.update_document_type(document_id, result.classification.document_type)

                if result.extraction is not None:
                    extraction_id = extractions.save_result(
                        document_id=document_id,
                        document_type=result.classification.document_type,
                        result=result.extraction,
                    )
                else:
                    extraction_id = None

                # This is the step that was missing: without it, nothing is
                # ever retrievable and /qa/answer has no evidence to work with.
                chunks_indexed = self._indexer.index_document(
                    document=parsed_document,
                    document_type=result.classification.document_type.value,
                )

                documents.update_status(document_id, DocumentStatus.READY)

                return {
                    "document_id": str(document_id),
                    "document_type": result.classification.document_type.value,
                    "classification_confidence": result.classification.confidence,
                    "status": DocumentStatus.READY.value,
                    "extraction_id": str(extraction_id) if extraction_id else None,
                    "chunks_indexed": chunks_indexed,
                }

            except Exception as exc:
                documents.update_status(document_id, DocumentStatus.FAILED)
                raise exc