from __future__ import annotations

from typing import Optional

from app.drift.models import DriftDimension, DriftResult, DriftSeverity, DriftThresholds
from app.drift.psi import bin_numeric, population_stability_index, proportions
from app.storage.models import BaselineSnapshotORM


class DocumentTypeDriftDetector:
    """15.3 -- has the mix of incoming document types shifted from the corpus-wide baseline?"""

    def __init__(self, thresholds: DriftThresholds):
        self._thresholds = thresholds

    def detect(self, baseline: BaselineSnapshotORM, current_counts: dict[str, int]) -> DriftResult:
        current_dist = proportions(current_counts)
        score = population_stability_index(baseline.document_type_distribution, current_dist)
        return DriftResult(
            dimension=DriftDimension.DOCUMENT_TYPE_DISTRIBUTION,
            key="document_type",
            score=score,
            severity=self._thresholds.classify(score),
            baseline_summary=baseline.document_type_distribution,
            current_summary=current_dist,
        )


class FieldPresenceDriftDetector:
    """15.4 -- has how often each field is populated shifted? 15.7 -- have new, unbaselined fields appeared?"""

    def __init__(self, thresholds: DriftThresholds):
        self._thresholds = thresholds

    def detect(self, baseline: BaselineSnapshotORM, current_presence: dict[str, float]) -> list[DriftResult]:
        results: list[DriftResult] = []
        fields = set(baseline.field_presence_rates) | set(current_presence)

        for field_name in fields:
            baseline_rate = baseline.field_presence_rates.get(field_name, 0.0)
            current_rate = current_presence.get(field_name, 0.0)
            # Presence is scored as a 2-bucket (present/absent) distribution -- PSI-comparable
            # to every other dimension here without a separate statistic just for this case.
            baseline_dist = {"present": baseline_rate, "absent": 1 - baseline_rate}
            current_dist = {"present": current_rate, "absent": 1 - current_rate}
            score = population_stability_index(baseline_dist, current_dist)
            results.append(
                DriftResult(
                    dimension=DriftDimension.FIELD_PRESENCE,
                    key=field_name,
                    score=score,
                    severity=self._thresholds.classify(score),
                    baseline_summary=baseline_dist,
                    current_summary=current_dist,
                )
            )

        new_fields = set(current_presence) - set(baseline.schema_keys)
        if new_fields:
            results.append(
                DriftResult(
                    dimension=DriftDimension.SCHEMA,
                    key="new_fields",
                    score=1.0,
                    severity=DriftSeverity.SIGNIFICANT,
                    baseline_summary={"schema_keys": baseline.schema_keys},
                    current_summary={"new_fields": sorted(new_fields)},
                )
            )
        return results


class NumericValueDriftDetector:
    """15.5 -- has the distribution of a numeric field (e.g. invoice total) shifted?"""

    def __init__(self, thresholds: DriftThresholds):
        self._thresholds = thresholds

    def detect(
        self, baseline: BaselineSnapshotORM, field_name: str, current_values: list[float]
    ) -> Optional[DriftResult]:
        field_baseline = baseline.numeric_field_bins.get(field_name)
        if field_baseline is None or not current_values:
            return None

        current_counts = bin_numeric(current_values, field_baseline["edges"])
        current_dist = proportions(current_counts)
        score = population_stability_index(field_baseline["distribution"], current_dist)

        return DriftResult(
            dimension=DriftDimension.NUMERIC_VALUE,
            key=field_name,
            score=score,
            severity=self._thresholds.classify(score),
            baseline_summary=field_baseline["distribution"],
            current_summary=current_dist,
        )


class ExtractionQualityDriftDetector:
    """15.8 -- is average extraction confidence slipping relative to baseline?"""

    def __init__(self, thresholds: DriftThresholds):
        self._thresholds = thresholds

    def detect(
        self, baseline: BaselineSnapshotORM, current_mean_confidence: Optional[float]
    ) -> Optional[DriftResult]:
        if baseline.mean_extraction_confidence is None or current_mean_confidence is None:
            return None

        # Confidence is already 0..1, so a relative drop is scored
        # directly (no PSI/binning needed) and classified on the same
        # 0.1/0.25 scale as every other dimension.
        score = max(0.0, baseline.mean_extraction_confidence - current_mean_confidence)
        return DriftResult(
            dimension=DriftDimension.EXTRACTION_QUALITY,
            key="mean_confidence",
            score=score,
            severity=self._thresholds.classify(score),
            baseline_summary={"mean_confidence": baseline.mean_extraction_confidence},
            current_summary={"mean_confidence": current_mean_confidence},
        )


class RetrievalQualityDriftDetector:
    """15.9 -- has offline retrieval eval quality (hit_rate@k / MRR, from Phase 14's eval script) degraded?"""

    def __init__(self, thresholds: DriftThresholds):
        self._thresholds = thresholds

    def detect(
        self,
        baseline: BaselineSnapshotORM,
        current_hit_rate: Optional[float],
        current_mrr: Optional[float],
    ) -> list[DriftResult]:
        results = []
        if baseline.retrieval_hit_rate is not None and current_hit_rate is not None:
            drop = max(0.0, baseline.retrieval_hit_rate - current_hit_rate)
            results.append(
                DriftResult(
                    dimension=DriftDimension.RETRIEVAL_QUALITY,
                    key="hit_rate_at_k",
                    score=drop,
                    severity=self._thresholds.classify(drop),
                    baseline_summary={"hit_rate_at_k": baseline.retrieval_hit_rate},
                    current_summary={"hit_rate_at_k": current_hit_rate},
                )
            )
        if baseline.retrieval_mrr is not None and current_mrr is not None:
            drop = max(0.0, baseline.retrieval_mrr - current_mrr)
            results.append(
                DriftResult(
                    dimension=DriftDimension.RETRIEVAL_QUALITY,
                    key="mrr",
                    score=drop,
                    severity=self._thresholds.classify(drop),
                    baseline_summary={"mrr": baseline.retrieval_mrr},
                    current_summary={"mrr": current_mrr},
                )
            )
        return results


class EmbeddingDriftDetector:
    """15.6 -- has the semantic content of indexed chunks shifted from the baseline centroid?"""

    def __init__(self, thresholds: DriftThresholds):
        self._thresholds = thresholds

    def detect(
        self, baseline: BaselineSnapshotORM, current_centroid: Optional[list[float]]
    ) -> Optional[DriftResult]:
        if baseline.embedding_centroid is None or current_centroid is None:
            return None

        distance = self._cosine_distance(baseline.embedding_centroid, current_centroid)
        return DriftResult(
            dimension=DriftDimension.EMBEDDING,
            key="chunk_centroid",
            score=distance,
            severity=self._thresholds.classify(distance),
            baseline_summary={"centroid_dim": len(baseline.embedding_centroid)},
            current_summary={"centroid_dim": len(current_centroid)},
        )

    @staticmethod
    def _cosine_distance(a: list[float], b: list[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(y * y for y in b) ** 0.5
        if norm_a == 0 or norm_b == 0:
            return 1.0
        return 1 - (dot / (norm_a * norm_b))