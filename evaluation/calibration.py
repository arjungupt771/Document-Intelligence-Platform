from evaluation.models import CalibrationMetrics, ConfidenceRecord


class CalibrationEvaluator:
    def evaluate(
        self,
        records: list[ConfidenceRecord],
    ) -> CalibrationMetrics:
        total_predictions = len(records)

        if total_predictions == 0:
            return CalibrationMetrics(
                total_predictions=0,
                correct_predictions=0,
                average_confidence=0.0,
                accuracy=0.0,
                calibration_error=0.0,
            )

        correct_predictions = sum(
            1
            for record in records
            if record.correct
        )

        average_confidence = sum(
            record.confidence
            for record in records
        ) / total_predictions

        accuracy = (
            correct_predictions / total_predictions
        )

        calibration_error = abs(
            average_confidence - accuracy
        )

        return CalibrationMetrics(
            total_predictions=total_predictions,
            correct_predictions=correct_predictions,
            average_confidence=average_confidence,
            accuracy=accuracy,
            calibration_error=calibration_error,
        )