import time
from dataclasses import dataclass
from typing import Optional

from app.classification.base import Classifier
from app.classification.models import ClassificationResult
from app.documents.models import DocumentType
from app.extraction.base import ExtractionResult
from app.extraction.errors import UnsupportedDocumentTypeError
from app.extraction.registry import ExtractorRegistry, default_extractor_registry
from app.observability.logging import get_logger, log_with_fields
from app.observability.metrics import (
    DOCUMENT_PROCESSED_TOTAL,
    DOCUMENT_PROCESSING_DURATION,
    EXTRACTION_CONFIDENCE,
    EXTRACTION_RESULT_TOTAL,
)
from app.parsing.models import ParsedDocument

logger = get_logger("app.extraction.pipeline")


@dataclass
class PipelineResult:
    classification: ClassificationResult
    extraction: Optional[ExtractionResult]


class ExtractionPipeline:
    def __init__(
        self,
        classifier: Classifier,
        extractor_registry: ExtractorRegistry = default_extractor_registry,
    ):
        self._classifier = classifier
        self._extractor_registry = extractor_registry

    def run(self, document: ParsedDocument) -> PipelineResult:
        start = time.perf_counter()
        classification = self._classifier.classify(document)

        if classification.document_type == DocumentType.UNKNOWN:
            DOCUMENT_PROCESSED_TOTAL.labels(document_type="unknown", status="unclassified").inc()
            DOCUMENT_PROCESSING_DURATION.labels(document_type="unknown").observe(time.perf_counter() - start)
            return PipelineResult(classification=classification, extraction=None)

        document_type_label = classification.document_type.value

        try:
            extractor = self._extractor_registry.get_extractor(classification.document_type)
        except UnsupportedDocumentTypeError:
            DOCUMENT_PROCESSED_TOTAL.labels(document_type=document_type_label, status="unsupported").inc()
            DOCUMENT_PROCESSING_DURATION.labels(document_type=document_type_label).observe(time.perf_counter() - start)
            return PipelineResult(classification=classification, extraction=None)

        try:
            extraction = extractor.extract(document)
        except Exception as exc:
            EXTRACTION_RESULT_TOTAL.labels(document_type=document_type_label, status="failed").inc()
            log_with_fields(
                logger, 40, "extraction_failed", document_type=document_type_label, error=str(exc)
            )
            raise
        finally:
            DOCUMENT_PROCESSING_DURATION.labels(document_type=document_type_label).observe(time.perf_counter() - start)

        EXTRACTION_RESULT_TOTAL.labels(document_type=document_type_label, status="completed").inc()
        EXTRACTION_CONFIDENCE.labels(document_type=document_type_label).observe(extraction.confidence)
        DOCUMENT_PROCESSED_TOTAL.labels(document_type=document_type_label, status="completed").inc()

        return PipelineResult(classification=classification, extraction=extraction)