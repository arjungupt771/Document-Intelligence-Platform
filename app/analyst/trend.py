import statistics

from app.analyst.models import Insight, InsightEvidence, InsightType, Severity
from app.documents.models import DocumentType
from app.storage.repository import ExtractionRepository

SIGNIFICANT_CHANGE_PCT = 0.5  # 50%
MIN_POINTS = 4


class TrendAnalyzer:
    """
    Portfolio-level analysis across every document of one type. Not an
    Analyzer/ComparativeAnalyzer (those work on one or two documents) --
    called directly by AnalystService.analyze_trend on demand, not as
    part of the per-document pipeline.
    """

    def __init__(self, extraction_repository: ExtractionRepository):
        self._extractions = extraction_repository

    def analyze(self, document_type: DocumentType) -> list[Insight]:
        rows = sorted(
            self._extractions.list_completed_by_document_type(document_type),
            key=lambda r: r.created_at,
        )

        points = []
        for row in rows:
            total = (row.data or {}).get("total")
            if total is None:
                continue
            try:
                points.append((row, float(total)))
            except (TypeError, ValueError):
                continue

        if len(points) < MIN_POINTS:
            return []

        insights = self._detect_jumps(points, document_type)
        overall = self._overall_direction(points, document_type)
        if overall is not None:
            insights.append(overall)
        return insights

    def _detect_jumps(self, points, document_type: DocumentType) -> list[Insight]:
        insights = []
        for (prev_row, prev_value), (row, value) in zip(points, points[1:]):
            if prev_value == 0:
                continue
            change = (value - prev_value) / abs(prev_value)
            if abs(change) < SIGNIFICANT_CHANGE_PCT:
                continue
            direction = "increase" if change > 0 else "decrease"
            insights.append(
                Insight(
                    type=InsightType.TREND,
                    severity=Severity.MEDIUM,
                    title=f"Sharp {direction} in {document_type.value} total",
                    description=(
                        f"Total went from {prev_value} to {value} ({change:+.0%}) between "
                        f"consecutive {document_type.value} documents."
                    ),
                    confidence=0.65,
                    evidence=[
                        InsightEvidence(
                            document_id=str(prev_row.document_id),
                            document_type=document_type.value,
                            text=f"total={prev_value}",
                            extraction_id=str(prev_row.id),
                        ),
                        InsightEvidence(
                            document_id=str(row.document_id),
                            document_type=document_type.value,
                            text=f"total={value}",
                            extraction_id=str(row.id),
                        ),
                    ],
                    document_ids=[str(prev_row.document_id), str(row.document_id)],
                    metadata={"pct_change": change},
                )
            )
        return insights

    def _overall_direction(self, points, document_type: DocumentType):
        values = [value for _, value in points]
        half = len(values) // 2
        first_half_avg = statistics.mean(values[:half])
        second_half_avg = statistics.mean(values[half:])
        if first_half_avg == 0:
            return None

        change = (second_half_avg - first_half_avg) / abs(first_half_avg)
        if abs(change) < 0.15:
            direction = "stable"
        elif change > 0:
            direction = "increasing"
        else:
            direction = "decreasing"

        rows = [row for row, _ in points]
        return Insight(
            type=InsightType.TREND,
            severity=Severity.LOW,
            title=f"{document_type.value.replace('_', ' ').capitalize()} totals are {direction}",
            description=(
                f"Average total moved from {first_half_avg:.2f} to {second_half_avg:.2f} across "
                f"{len(points)} documents ({change:+.0%})."
            ),
            confidence=0.6,
            evidence=[
                InsightEvidence(
                    document_id=str(rows[0].document_id),
                    document_type=document_type.value,
                    text=f"n={len(points)}, first_half_avg={first_half_avg:.2f}, second_half_avg={second_half_avg:.2f}",
                    extraction_id=str(rows[0].id),
                )
            ],
            document_ids=[str(row.document_id) for row in rows],
            metadata={"pct_change": change, "n": len(points)},
        )