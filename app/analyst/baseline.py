import statistics
import uuid
from typing import Optional

from app.analyst.models import BaselineStats
from app.documents.models import DocumentType
from app.storage.repository import ExtractionRepository

MIN_SAMPLE_SIZE = 3


class BaselineBuilder:
    """Historical mean/stdev of `total` for a document type -- feeds both anomaly and trend analysis."""

    def __init__(self, extraction_repository: ExtractionRepository):
        self._extractions = extraction_repository

    def build(
        self,
        document_type: DocumentType,
        exclude_document_id: Optional[uuid.UUID] = None,
    ) -> Optional[BaselineStats]:
        rows = self._extractions.list_completed_by_document_type(
            document_type, exclude_document_id=exclude_document_id
        )
        values = self._extract_totals(rows)
        if len(values) < MIN_SAMPLE_SIZE:
            return None

        return BaselineStats(
            mean=statistics.mean(values),
            stdev=statistics.pstdev(values) if len(values) > 1 else 0.0,
            sample_size=len(values),
        )

    @staticmethod
    def _extract_totals(rows) -> list[float]:
        values = []
        for row in rows:
            total = (row.data or {}).get("total")
            if total is None:
                continue
            try:
                values.append(float(total))
            except (TypeError, ValueError):
                continue
        return values