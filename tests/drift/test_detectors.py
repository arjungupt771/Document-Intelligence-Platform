from app.drift.detectors import (
    DocumentTypeDriftDetector,
    EmbeddingDriftDetector,
    ExtractionQualityDriftDetector,
    FieldPresenceDriftDetector,
    NumericValueDriftDetector,
    RetrievalQualityDriftDetector,
)
from app.drift.models import DriftSeverity, DriftThresholds
from app.storage.models import BaselineSnapshotORM


def _baseline(**overrides) -> BaselineSnapshotORM:
    defaults = dict(
        document_type_distribution={"invoice": 0.9, "contract": 0.1},
        field_presence_rates={"vendor": 0.95},
        numeric_field_bins={"total": {"edges": [100, 500], "distribution": {"<100": 0.2, "100-500": 0.5, ">500": 0.3}}},
        schema_keys=["vendor", "total"],
        embedding_centroid=[1.0, 0.0],
        mean_extraction_confidence=0.9,
        retrieval_hit_rate=0.8,
        retrieval_mrr=0.7,
        sample_size=100,
    )
    defaults.update(overrides)
    return BaselineSnapshotORM(**defaults)


THRESHOLDS = DriftThresholds(moderate=0.1, significant=0.25)


class TestDocumentTypeDriftDetector:
    def test_detects_no_drift_for_matching_distribution(self):
        result = DocumentTypeDriftDetector(THRESHOLDS).detect(_baseline(), {"invoice": 90, "contract": 10})
        assert result.severity == DriftSeverity.NONE

    def test_detects_drift_for_shifted_distribution(self):
        result = DocumentTypeDriftDetector(THRESHOLDS).detect(_baseline(), {"invoice": 10, "contract": 90})
        assert result.severity == DriftSeverity.SIGNIFICANT


class TestFieldPresenceDriftDetector:
    def test_flags_dropped_field_presence(self):
        results = FieldPresenceDriftDetector(THRESHOLDS).detect(_baseline(), {"vendor": 0.3})
        vendor_result = next(r for r in results if r.key == "vendor")
        assert vendor_result.severity != DriftSeverity.NONE

    def test_flags_new_field_as_schema_drift(self):
        results = FieldPresenceDriftDetector(THRESHOLDS).detect(_baseline(), {"vendor": 0.95, "new_field": 0.5})
        schema_results = [r for r in results if r.dimension.value == "schema"]
        assert len(schema_results) == 1
        assert schema_results[0].severity == DriftSeverity.SIGNIFICANT


class TestNumericValueDriftDetector:
    def test_returns_none_for_unbaselined_field(self):
        result = NumericValueDriftDetector(THRESHOLDS).detect(_baseline(), "tax", [1, 2, 3])
        assert result is None

    def test_flags_shifted_distribution(self):
        result = NumericValueDriftDetector(THRESHOLDS).detect(_baseline(), "total", [5000] * 20)
        assert result is not None
        assert result.severity != DriftSeverity.NONE


class TestExtractionQualityDriftDetector:
    def test_flags_confidence_drop(self):
        result = ExtractionQualityDriftDetector(THRESHOLDS).detect(_baseline(), current_mean_confidence=0.5)
        assert result is not None
        assert result.severity != DriftSeverity.NONE

    def test_no_result_when_confidence_stable(self):
        result = ExtractionQualityDriftDetector(THRESHOLDS).detect(_baseline(), current_mean_confidence=0.92)
        assert result.severity == DriftSeverity.NONE


class TestRetrievalQualityDriftDetector:
    def test_flags_hit_rate_drop(self):
        results = RetrievalQualityDriftDetector(THRESHOLDS).detect(
            _baseline(), current_hit_rate=0.4, current_mrr=0.7
        )
        hit_rate_result = next(r for r in results if r.key == "hit_rate_at_k")
        assert hit_rate_result.severity != DriftSeverity.NONE


class TestEmbeddingDriftDetector:
    def test_flags_centroid_shift(self):
        result = EmbeddingDriftDetector(THRESHOLDS).detect(_baseline(), current_centroid=[0.0, 1.0])
        assert result is not None
        assert result.severity == DriftSeverity.SIGNIFICANT

    def test_no_drift_for_identical_centroid(self):
        result = EmbeddingDriftDetector(THRESHOLDS).detect(_baseline(), current_centroid=[1.0, 0.0])
        assert result.severity == DriftSeverity.NONE