"""Pass/fail gates for CI. Keep these numbers in one place so a threshold
change is a one-line diff and shows up clearly in review."""
from dataclasses import dataclass

from evaluation.models import EvaluationMetrics


@dataclass(frozen=True)
class QualityThresholds:
    min_field_accuracy: float = 0.85
    min_precision: float = 0.85
    min_recall: float = 0.80
    max_hallucinated_field_rate: float = 0.05
    max_missing_field_rate: float = 0.15

    min_retrieval_hit_rate: float = 0.80
    min_grounding_rate: float = 0.90  # fraction of answers whose claims are evidence-backed
    max_hallucination_rate: float = 0.05  # fraction of answers with unsupported claims


@dataclass(frozen=True)
class ThresholdViolation:
    metric: str
    actual: float
    threshold: float
    direction: str  # "min" | "max"


def check_extraction_quality(
    metrics: EvaluationMetrics, thresholds: QualityThresholds = QualityThresholds()
) -> list[ThresholdViolation]:
    violations = []

    checks = [
        ("field_accuracy", metrics.field_accuracy, thresholds.min_field_accuracy, "min"),
        ("precision", metrics.precision, thresholds.min_precision, "min"),
        ("recall", metrics.recall, thresholds.min_recall, "min"),
        ("hallucinated_field_rate", metrics.hallucinated_field_rate, thresholds.max_hallucinated_field_rate, "max"),
        ("missing_field_rate", metrics.missing_field_rate, thresholds.max_missing_field_rate, "max"),
    ]

    for name, actual, threshold, direction in checks:
        failed = actual < threshold if direction == "min" else actual > threshold
        if failed:
            violations.append(ThresholdViolation(name, actual, threshold, direction))

    return violations