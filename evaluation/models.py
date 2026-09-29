from typing import Any

from pydantic import BaseModel, Field


class GroundTruth(BaseModel):
    fields: dict[str, Any] = Field(default_factory=dict)


class EvaluationCase(BaseModel):
    document: str
    document_type: str
    ground_truth: GroundTruth


class FieldComparison(BaseModel):
    field: str
    expected: Any = None
    predicted: Any = None
    status: str


class ComparisonResult(BaseModel):
    fields: list[FieldComparison] = Field(default_factory=list)


class EvaluationMetrics(BaseModel):
    total_expected_fields: int
    total_predicted_fields: int
    matched_fields: int
    mismatched_fields: int
    missing_fields: int
    extra_fields: int

    field_accuracy: float
    precision: float
    recall: float
    f1: float

    missing_field_rate: float
    hallucinated_field_rate: float

class EvaluationResult(BaseModel):
    comparison: ComparisonResult
    metrics: EvaluationMetrics

class ConfidenceRecord(BaseModel):
    field: str
    confidence: float = Field(ge=0.0, le=1.0)
    correct: bool

class CalibrationMetrics(BaseModel):
    total_predictions: int
    correct_predictions: int
    average_confidence: float
    accuracy: float
    calibration_error: float