from evaluation.calibration import CalibrationEvaluator
from evaluation.models import ConfidenceRecord
import pytest
from pydantic import ValidationError

def test_confidence_cannot_be_greater_than_one():
    with pytest.raises(ValidationError):
        ConfidenceRecord(
            field="total",
            confidence=1.2,
            correct=True,
        )


def test_confidence_cannot_be_negative():
    with pytest.raises(ValidationError):
        ConfidenceRecord(
            field="total",
            confidence=-0.1,
            correct=False,
        )


def test_confidence_boundary_values_are_valid():
    low = ConfidenceRecord(
        field="total",
        confidence=0.0,
        correct=False,
    )

    high = ConfidenceRecord(
        field="total",
        confidence=1.0,
        correct=True,
    )

    assert low.confidence == 0.0
    assert high.confidence == 1.0

def test_calibration_evaluator():
    records = [
        ConfidenceRecord(
            field="vendor",
            confidence=0.95,
            correct=True,
        ),
        ConfidenceRecord(
            field="invoice_number",
            confidence=0.90,
            correct=True,
        ),
        ConfidenceRecord(
            field="total",
            confidence=0.80,
            correct=False,
        ),
    ]

    evaluator = CalibrationEvaluator()

    result = evaluator.evaluate(records)

    assert result.total_predictions == 3
    assert result.correct_predictions == 2

    assert result.average_confidence == (0.95 + 0.90 + 0.80) / 3
    assert result.accuracy == 2 / 3

    expected_error = abs(
        ((0.95 + 0.90 + 0.80) / 3)
        - (2 / 3)
    )

    assert result.calibration_error == expected_error


def test_perfect_calibration():
    records = [
        ConfidenceRecord(
            field="vendor",
            confidence=1.0,
            correct=True,
        ),
        ConfidenceRecord(
            field="total",
            confidence=1.0,
            correct=True,
        ),
    ]

    result = CalibrationEvaluator().evaluate(records)

    assert result.total_predictions == 2
    assert result.correct_predictions == 2
    assert result.average_confidence == 1.0
    assert result.accuracy == 1.0
    assert result.calibration_error == 0.0


def test_empty_calibration():
    result = CalibrationEvaluator().evaluate([])

    assert result.total_predictions == 0
    assert result.correct_predictions == 0
    assert result.average_confidence == 0.0
    assert result.accuracy == 0.0
    assert result.calibration_error == 0.0