from app.analyst.base import Analyzer
from app.analyst.models import AnalysisContext, Insight, InsightEvidence, InsightType, Severity

Z_SCORE_THRESHOLD = 2.5


class AnomalyAnalyzer(Analyzer):
    """Flags a document's total as statistically unusual against its historical peers."""

    def __init__(self, z_score_threshold: float = Z_SCORE_THRESHOLD):
        self._threshold = z_score_threshold

    def analyze(self, context: AnalysisContext) -> list[Insight]:
        if context.baseline is None:
            return []

        total = (context.extraction.data or {}).get("total")
        if total is None:
            return []

        try:
            total_value = float(total)
        except (TypeError, ValueError):
            return []

        z = context.baseline.z_score(total_value)
        if z is None or abs(z) < self._threshold:
            return []

        direction = "higher" if z > 0 else "lower"
        return [
            Insight(
                type=InsightType.ANOMALY,
                severity=Severity.HIGH if abs(z) >= self._threshold * 1.4 else Severity.MEDIUM,
                title=f"Unusually {direction} total amount",
                description=(
                    f"Total of {total_value} is {abs(z):.2f} standard deviations {direction} than the "
                    f"historical average of {context.baseline.mean:.2f} (n={context.baseline.sample_size})."
                ),
                confidence=min(0.5 + abs(z) / 10, 0.95),
                evidence=[
                    InsightEvidence(
                        document_id=str(context.document.id),
                        document_type=context.document.document_type.value,
                        text=(
                            f"total={total_value}, baseline_mean={context.baseline.mean}, "
                            f"baseline_stdev={context.baseline.stdev}"
                        ),
                        field_path="total",
                        extraction_id=str(context.extraction.id),
                    )
                ],
                metadata={"z_score": z, "baseline_n": context.baseline.sample_size},
            )
        ]