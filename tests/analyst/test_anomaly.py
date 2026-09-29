from app.analyst.anomaly import AnomalyAnalyzer
from app.analyst.models import AnalysisContext, BaselineStats
from app.documents.models import DocumentType
from tests.analyst.conftest import make_document, make_extraction


class TestAnomalyAnalyzer:
    def test_flags_outlier_total(self):
        context = AnalysisContext(
            document=make_document(DocumentType.INVOICE),
            extraction=make_extraction({"total": "10000"}, DocumentType.INVOICE),
            baseline=BaselineStats(mean=500, stdev=50, sample_size=10),
        )

        insights = AnomalyAnalyzer().analyze(context)

        assert len(insights) == 1
        assert "higher" in insights[0].title

    def test_no_insight_without_baseline(self):
        context = AnalysisContext(
            document=make_document(DocumentType.INVOICE),
            extraction=make_extraction({"total": "10000"}, DocumentType.INVOICE),
            baseline=None,
        )

        assert AnomalyAnalyzer().analyze(context) == []

    def test_no_insight_within_normal_range(self):
        context = AnalysisContext(
            document=make_document(DocumentType.INVOICE),
            extraction=make_extraction({"total": "510"}, DocumentType.INVOICE),
            baseline=BaselineStats(mean=500, stdev=50, sample_size=10),
        )

        assert AnomalyAnalyzer().analyze(context) == []