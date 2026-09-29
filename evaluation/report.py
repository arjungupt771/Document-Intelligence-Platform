from evaluation.models import EvaluationMetrics, EvaluationResult


class EvaluationReport:
    def generate(
        self,
        results: dict[str, EvaluationResult],
    ) -> EvaluationMetrics:
        total_expected = sum(
            result.metrics.total_expected_fields
            for result in results.values()
        )

        total_predicted = sum(
            result.metrics.total_predicted_fields
            for result in results.values()
        )

        matched = sum(
            result.metrics.matched_fields
            for result in results.values()
        )

        mismatched = sum(
            result.metrics.mismatched_fields
            for result in results.values()
        )

        missing = sum(
            result.metrics.missing_fields
            for result in results.values()
        )

        extra = sum(
            result.metrics.extra_fields
            for result in results.values()
        )

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