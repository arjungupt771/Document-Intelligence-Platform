from typing import Any

from evaluation.evaluator import Evaluator
from evaluation.models import EvaluationCase, EvaluationResult


class EvaluationRunner:
    def __init__(self, evaluator: Evaluator | None = None) -> None:
        self.evaluator = evaluator or Evaluator()

    def evaluate_case(
        self,
        case: EvaluationCase,
        predicted: dict[str, Any],
    ) -> EvaluationResult:
        return self.evaluator.evaluate(
            expected=case.ground_truth.fields,
            predicted=predicted,
        )

    def evaluate_dataset(
        self,
        cases: list[EvaluationCase],
        predictions: dict[str, dict[str, Any]],
    ) -> dict[str, EvaluationResult]:
        results: dict[str, EvaluationResult] = {}

        for case in cases:
            if case.document not in predictions:
                continue

            results[case.document] = self.evaluate_case(
                case,
                predictions[case.document],
            )

        return results