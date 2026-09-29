from __future__ import annotations

from typing import Optional

from app.documents.models import DocumentType
from app.drift.baseline_builder import NUMERIC_FIELDS_BY_TYPE, BaselineSnapshotBuilder
from app.drift.detectors import (
    DocumentTypeDriftDetector,
    EmbeddingDriftDetector,
    ExtractionQualityDriftDetector,
    FieldPresenceDriftDetector,
    NumericValueDriftDetector,
    RetrievalQualityDriftDetector,
)
from app.drift.embedding_sampler import ChunkEmbeddingSampler
from app.drift.models import DriftResult, DriftSeverity, DriftThresholds
from app.storage.repository import (
    BaselineSnapshotRepository,
    DocumentRepository,
    DriftAlertRepository,
    DriftResultRepository,
    ExtractionRepository,
)


class DriftMonitoringService:
    def __init__(
        self,
        document_repository: DocumentRepository,
        extraction_repository: ExtractionRepository,
        baseline_repository: BaselineSnapshotRepository,
        drift_result_repository: DriftResultRepository,
        drift_alert_repository: DriftAlertRepository,
        thresholds: Optional[DriftThresholds] = None,
        embedding_sampler: Optional[ChunkEmbeddingSampler] = None,
    ):
        self._documents = document_repository
        self._extractions = extraction_repository
        self._baselines = baseline_repository
        self._drift_results = drift_result_repository
        self._drift_alerts = drift_alert_repository
        self._thresholds = thresholds or DriftThresholds.from_env()
        self._embedding_sampler = embedding_sampler

        self._document_type_detector = DocumentTypeDriftDetector(self._thresholds)
        self._field_presence_detector = FieldPresenceDriftDetector(self._thresholds)
        self._numeric_detector = NumericValueDriftDetector(self._thresholds)
        self._quality_detector = ExtractionQualityDriftDetector(self._thresholds)
        self._retrieval_detector = RetrievalQualityDriftDetector(self._thresholds)
        self._embedding_detector = EmbeddingDriftDetector(self._thresholds)

    def establish_baseline(self, document_type: DocumentType) -> Optional[str]:
        builder = BaselineSnapshotBuilder(self._documents, self._extractions)
        snapshot = builder.build(document_type)
        if snapshot is None:
            return None

        if self._embedding_sampler is not None:
            snapshot.embedding_centroid = self._embedding_sampler.sample_centroid()

        return str(self._baselines.save(document_type, snapshot))

    def check_drift(
        self,
        document_type: DocumentType,
        current_hit_rate: Optional[float] = None,
        current_mrr: Optional[float] = None,
        persist: bool = True,
    ) -> list[DriftResult]:
        baseline = self._baselines.get_active(document_type)
        if baseline is None:
            return []

        rows = self._extractions.list_completed_by_document_type(document_type)
        results: list[DriftResult] = []

        type_counts = self._documents.count_by_document_type()
        results.append(self._document_type_detector.detect(baseline, type_counts))

        current_presence = self._compute_presence(rows)
        results.extend(self._field_presence_detector.detect(baseline, current_presence))

        for field_name in NUMERIC_FIELDS_BY_TYPE.get(document_type, []):
            values = self._numeric_values(rows, field_name)
            result = self._numeric_detector.detect(baseline, field_name, values)
            if result is not None:
                results.append(result)

        confidences = [row.confidence for row in rows if row.confidence is not None]
        mean_confidence = sum(confidences) / len(confidences) if confidences else None
        quality_result = self._quality_detector.detect(baseline, mean_confidence)
        if quality_result is not None:
            results.append(quality_result)

        results.extend(self._retrieval_detector.detect(baseline, current_hit_rate, current_mrr))

        if self._embedding_sampler is not None:
            current_centroid = self._embedding_sampler.sample_centroid()
            embedding_result = self._embedding_detector.detect(baseline, current_centroid)
            if embedding_result is not None:
                results.append(embedding_result)

        if persist:
            for result in results:
                result_id = self._drift_results.save(result)
                if result.severity != DriftSeverity.NONE:
                    self._raise_alert(result_id, result)

        return results

    def _raise_alert(self, drift_result_id, result: DriftResult) -> None:
        message = (
            f"{result.severity.value.upper()} drift on {result.dimension.value} "
            f"({result.key}): score={result.score:.3f}"
        )
        self._drift_alerts.save(drift_result_id, message)

    @staticmethod
    def _compute_presence(rows) -> dict[str, float]:
        if not rows:
            return {}
        counts: dict[str, int] = {}
        for row in rows:
            for key, value in (row.data or {}).items():
                if value not in (None, "", []):
                    counts[key] = counts.get(key, 0) + 1
        return {key: count / len(rows) for key, count in counts.items()}

    @staticmethod
    def _numeric_values(rows, field_name: str) -> list[float]:
        values = []
        for row in rows:
            value = (row.data or {}).get(field_name)
            if value is None:
                continue
            try:
                values.append(float(value))
            except (TypeError, ValueError):
                continue
        return values