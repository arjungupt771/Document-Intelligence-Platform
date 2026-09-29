from typing import Any

from evaluation.models import (
    ComparisonResult,
    EvaluationMetrics,
    FieldComparison,
    EvaluationResult,
)
from evaluation.value_comparator import ValueComparator


class MetricsCalculator:
    def calculate(self, result: ComparisonResult) -> EvaluationMetrics:
        matched = sum(
            1 for field in result.fields if field.status == "match"
        )
        mismatched = sum(
            1 for field in result.fields if field.status == "mismatch"
        )
        missing = sum(
            1 for field in result.fields if field.status == "missing"
        )
        extra = sum(
            1 for field in result.fields if field.status == "extra"
        )

        total_expected = matched + mismatched + missing
        total_predicted = matched + mismatched + extra

        field_accuracy = (
            matched / total_expected
            if total_expected
            else 0.0
        )

        precision = (
            matched / total_predicted
            if total_predicted
            else 0.0
        )

        recall = (
            matched / total_expected
            if total_expected
            else 0.0
        )

        f1 = (
            2 * precision * recall / (precision + recall)
            if precision + recall
            else 0.0
        )

        missing_field_rate = (
            missing / total_expected
            if total_expected
            else 0.0
        )

        hallucinated_field_rate = (
            extra / total_predicted
            if total_predicted
            else 0.0
        )

        return EvaluationMetrics(
            total_expected_fields=total_expected,
            total_predicted_fields=total_predicted,
            matched_fields=matched,
            mismatched_fields=mismatched,
            missing_fields=missing,
            extra_fields=extra,
            field_accuracy=field_accuracy,
            precision=precision,
            recall=recall,
            f1=f1,
            missing_field_rate=missing_field_rate,
            hallucinated_field_rate=hallucinated_field_rate,
        )

class FieldComparator:
    def __init__(self) -> None:
        self.value_comparator = ValueComparator()

    def compare(
        self,
        expected: dict[str, Any],
        predicted: dict[str, Any],
    ) -> ComparisonResult:
        comparisons: list[FieldComparison] = []

        all_fields = set(expected) | set(predicted)

        for field in sorted(all_fields):
            expected_value = expected.get(field)
            predicted_value = predicted.get(field)

            if field not in predicted:
                status = "missing"
            elif field not in expected:
                status = "extra"
            elif self.value_comparator.compare(
                expected_value,
                predicted_value,
            ):
                status = "match"
            else:
                status = "mismatch"

            comparisons.append(
                FieldComparison(
                    field=field,
                    expected=expected_value,
                    predicted=predicted_value,
                    status=status,
                )
            )

        return ComparisonResult(fields=comparisons)

class Evaluator:
    def __init__(self) -> None:
        self.comparator = FieldComparator()
        self.metrics_calculator = MetricsCalculator()

    def evaluate(
        self,
        expected: dict[str, Any],
        predicted: dict[str, Any],
    ):
        comparison = self.comparator.compare(
            expected=expected,
            predicted=predicted,
        )

        metrics = self.metrics_calculator.calculate(comparison)

        return EvaluationResult(
            comparison=comparison,
            metrics=metrics,
        )