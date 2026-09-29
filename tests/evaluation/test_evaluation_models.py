import pytest
from pydantic import ValidationError

from evaluation.models import (
    ComparisonResult,
    EvaluationCase,
    FieldComparison,
    GroundTruth,
)

def test_ground_truth_creation():
    ground_truth = GroundTruth(
        fields={
            "vendor": "ACME Corporation",
            "total": 354000,
        }
    )

    assert ground_truth.fields["vendor"] == "ACME Corporation"
    assert ground_truth.fields["total"] == 354000


def test_evaluation_case_creation():
    case = EvaluationCase(
        document="invoice_001.pdf",
        document_type="invoice",
        ground_truth=GroundTruth(
            fields={
                "vendor": "ACME Corporation",
                "total": 354000,
            }
        ),
    )

    assert case.document == "invoice_001.pdf"
    assert case.document_type == "invoice"
    assert case.ground_truth.fields["total"] == 354000


def test_evaluation_case_requires_document():
    with pytest.raises(ValidationError):
        EvaluationCase(
            document_type="invoice",
            ground_truth=GroundTruth(fields={}),
        )

def test_field_comparison_creation():
    comparison = FieldComparison(
        field="total",
        expected=354000,
        predicted=354000,
        status="match",
    )

    assert comparison.field == "total"
    assert comparison.expected == 354000
    assert comparison.predicted == 354000
    assert comparison.status == "match"


def test_comparison_result_creation():
    result = ComparisonResult(
        fields=[
            FieldComparison(
                field="vendor",
                expected="ACME Corporation",
                predicted="ACME Corporation",
                status="match",
            ),
            FieldComparison(
                field="total",
                expected=354000,
                predicted=350000,
                status="mismatch",
            ),
        ]
    )

    assert len(result.fields) == 2
    assert result.fields[0].status == "match"
    assert result.fields[1].status == "mismatch"