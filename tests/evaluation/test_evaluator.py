from evaluation.evaluator import FieldComparator
from evaluation.evaluator import MetricsCalculator
from evaluation.models import ComparisonResult


def test_metrics_with_no_fields():
    result = ComparisonResult(fields=[])

    metrics = MetricsCalculator().calculate(result)

    assert metrics.total_expected_fields == 0
    assert metrics.total_predicted_fields == 0

    assert metrics.matched_fields == 0
    assert metrics.mismatched_fields == 0
    assert metrics.missing_fields == 0
    assert metrics.extra_fields == 0

    assert metrics.field_accuracy == 0.0
    assert metrics.precision == 0.0
    assert metrics.recall == 0.0
    assert metrics.f1 == 0.0

    assert metrics.missing_field_rate == 0.0
    assert metrics.hallucinated_field_rate == 0.0

def test_all_fields_match():
    comparator = FieldComparator()

    result = comparator.compare(
        expected={
            "vendor": "ACME Corporation",
            "total": 354000,
        },
        predicted={
            "vendor": "ACME Corporation",
            "total": 354000,
        },
    )

    assert len(result.fields) == 2
    assert all(item.status == "match" for item in result.fields)


def test_detects_mismatch():
    comparator = FieldComparator()

    result = comparator.compare(
        expected={
            "vendor": "ACME Corporation",
            "total": 354000,
        },
        predicted={
            "vendor": "ACME Corporation",
            "total": 350000,
        },
    )

    total_result = next(
        item for item in result.fields if item.field == "total"
    )

    assert total_result.status == "mismatch"
    assert total_result.expected == 354000
    assert total_result.predicted == 350000


def test_detects_missing_field():
    comparator = FieldComparator()

    result = comparator.compare(
        expected={
            "vendor": "ACME Corporation",
            "total": 354000,
        },
        predicted={
            "vendor": "ACME Corporation",
        },
    )

    total_result = next(
        item for item in result.fields if item.field == "total"
    )

    assert total_result.status == "missing"


def test_detects_extra_field():
    comparator = FieldComparator()

    result = comparator.compare(
        expected={
            "vendor": "ACME Corporation",
        },
        predicted={
            "vendor": "ACME Corporation",
            "tax": 18000,
        },
    )

    tax_result = next(
        item for item in result.fields if item.field == "tax"
    )

    assert tax_result.status == "extra"


from evaluation.evaluator import Evaluator


def test_evaluator_runs_complete_evaluation():
    evaluator = Evaluator()

    result = evaluator.evaluate(
        expected={
            "vendor": "ACME Corporation",
            "total": 354000,
        },
        predicted={
            "vendor": "ACME Corporation",
            "total": 350000,
        },
    )

    assert result.comparison.fields

    assert result.metrics.total_expected_fields == 2
    assert result.metrics.total_predicted_fields == 2

    assert result.metrics.matched_fields == 1
    assert result.metrics.mismatched_fields == 1
    assert result.metrics.missing_fields == 0
    assert result.metrics.extra_fields == 0

    assert result.metrics.field_accuracy == 0.5
    assert result.metrics.precision == 0.5
    assert result.metrics.recall == 0.5
    assert result.metrics.f1 == 0.5

def test_evaluator_uses_value_comparator_for_strings():
    evaluator = Evaluator()

    result = evaluator.evaluate(
        expected={
            "vendor": " ACME Corporation ",
        },
        predicted={
            "vendor": "acme corporation",
        },
    )

    assert result.metrics.matched_fields == 1
    assert result.metrics.mismatched_fields == 0

def test_evaluator_uses_value_comparator_for_numbers():
    evaluator = Evaluator()

    result = evaluator.evaluate(
        expected={
            "total": 354000,
        },
        predicted={
            "total": 354000.00,
        },
    )

    assert result.metrics.matched_fields == 1
    assert result.metrics.mismatched_fields == 0

def test_evaluator_uses_value_comparator_for_dates():
    evaluator = Evaluator()

    result = evaluator.evaluate(
        expected={
            "invoice_date": "2026-09-21",
        },
        predicted={
            "invoice_date": "21/09/2026",
        },
    )

    assert result.metrics.matched_fields == 1
    assert result.metrics.mismatched_fields == 0