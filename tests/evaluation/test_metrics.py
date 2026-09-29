from evaluation.evaluator import MetricsCalculator
from evaluation.models import (
    ComparisonResult,
    EvaluationMetrics,
    EvaluationResult,
    FieldComparison,
)

def test_metrics_calculation():
    result = ComparisonResult(
        fields=[
            FieldComparison(
                field="vendor",
                expected="ACME",
                predicted="ACME",
                status="match",
            ),
            FieldComparison(
                field="total",
                expected=354000,
                predicted=350000,
                status="mismatch",
            ),
            FieldComparison(
                field="invoice_number",
                expected="INV-1042",
                predicted=None,
                status="missing",
            ),
            FieldComparison(
                field="tax",
                expected=None,
                predicted=18000,
                status="extra",
            ),
        ]
    )

    metrics = MetricsCalculator().calculate(result)

    assert metrics.total_expected_fields == 3
    assert metrics.total_predicted_fields == 3

    assert metrics.matched_fields == 1
    assert metrics.mismatched_fields == 1
    assert metrics.missing_fields == 1
    assert metrics.extra_fields == 1

    assert metrics.field_accuracy == 1 / 3
    assert metrics.precision == 1 / 3
    assert metrics.recall == 1 / 3

    assert metrics.f1 == 1 / 3

    assert metrics.missing_field_rate == 1 / 3
    assert metrics.hallucinated_field_rate == 1 / 3

def test_evaluation_result_creation():
    comparison = ComparisonResult(
        fields=[
            FieldComparison(
                field="vendor",
                expected="ACME",
                predicted="ACME",
                status="match",
            )
        ]
    )

    metrics = EvaluationMetrics(
        total_expected_fields=1,
        total_predicted_fields=1,
        matched_fields=1,
        mismatched_fields=0,
        missing_fields=0,
        extra_fields=0,
        field_accuracy=1.0,
        precision=1.0,
        recall=1.0,
        f1=1.0,
        missing_field_rate=0.0,
        hallucinated_field_rate=0.0,
    )

    result = EvaluationResult(
        comparison=comparison,
        metrics=metrics,
    )

    assert result.comparison.fields[0].status == "match"
    assert result.metrics.f1 == 1.0