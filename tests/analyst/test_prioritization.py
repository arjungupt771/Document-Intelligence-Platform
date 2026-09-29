from app.analyst.models import Insight, InsightType, Severity
from app.analyst.prioritization import InsightPrioritizer


def _insight(severity, confidence, title="t"):
    return Insight(
        type=InsightType.RISK,
        severity=severity,
        title=title,
        description="d",
        confidence=confidence,
        document_ids=["doc-1"],
    )


class TestInsightPrioritizer:
    def test_sorts_by_severity_and_confidence(self):
        low = _insight(Severity.LOW, 0.9, title="low")
        high = _insight(Severity.HIGH, 0.5, title="high")

        result = InsightPrioritizer().prioritize([low, high])

        assert result[0].title == "high"
        assert result[0].priority_score > result[1].priority_score

    def test_dedupes_same_type_title_and_documents(self):
        a = _insight(Severity.MEDIUM, 0.6, title="dup")
        b = _insight(Severity.MEDIUM, 0.9, title="dup")

        result = InsightPrioritizer().prioritize([a, b])

        assert len(result) == 1
        assert result[0].confidence == 0.9