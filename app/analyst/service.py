from __future__ import annotations

import uuid
from typing import Optional

from app.analyst.anomaly import AnomalyAnalyzer
from app.analyst.base import Analyzer, ComparativeAnalyzer
from app.analyst.baseline import BaselineBuilder
from app.analyst.completeness import CompletenessAnalyzer
from app.analyst.cross_document import InvoicePurchaseOrderMatcher
from app.analyst.financial import FinancialAnalyzer
from app.analyst.generator import GroundedInsightGenerator
from app.analyst.models import AnalysisContext, AnalystReport, Insight
from app.analyst.prioritization import InsightPrioritizer
from app.analyst.risk import RiskAnalyzer
from app.analyst.trend import TrendAnalyzer
from app.documents.models import DocumentType
from app.storage.models import ExtractionStatusEnum
from app.storage.repository import DocumentRepository, ExtractionRepository, InsightRepository


class AnalystService:
    def __init__(
        self,
        document_repository: DocumentRepository,
        extraction_repository: ExtractionRepository,
        insight_repository: InsightRepository,
        analyzers: Optional[list[Analyzer]] = None,
        comparative_analyzers: Optional[list[ComparativeAnalyzer]] = None,
        prioritizer: Optional[InsightPrioritizer] = None,
        narrative_generator: Optional[GroundedInsightGenerator] = None,
    ):
        self._documents = document_repository
        self._extractions = extraction_repository
        self._insights = insight_repository
        self._baseline_builder = BaselineBuilder(extraction_repository)
        self._trend_analyzer = TrendAnalyzer(extraction_repository)
        self._prioritizer = prioritizer or InsightPrioritizer()
        self._narrative_generator = narrative_generator

        self._analyzers = analyzers or [
            CompletenessAnalyzer(),
            FinancialAnalyzer(),
            AnomalyAnalyzer(),
            RiskAnalyzer(),
        ]
        self._comparative_analyzers = comparative_analyzers or [InvoicePurchaseOrderMatcher()]

    def analyze_document(self, document_id: uuid.UUID, persist: bool = True) -> AnalystReport:
        context = self._build_context(document_id)
        if context is None:
            return AnalystReport(document_id=str(document_id), insights=[])

        insights: list[Insight] = []
        for analyzer in self._analyzers:
            insights.extend(analyzer.analyze(context))

        insights = self._finish(insights, persist)
        return AnalystReport(document_id=str(document_id), insights=insights)

    def compare_documents(
        self, document_id_a: uuid.UUID, document_id_b: uuid.UUID, persist: bool = True
    ) -> list[Insight]:
        context_a = self._build_context(document_id_a)
        context_b = self._build_context(document_id_b)
        if context_a is None or context_b is None:
            return []

        insights: list[Insight] = []
        for analyzer in self._comparative_analyzers:
            insights.extend(analyzer.compare(context_a, context_b))

        return self._finish(insights, persist)

    def analyze_trend(self, document_type: DocumentType, persist: bool = True) -> list[Insight]:
        insights = self._trend_analyzer.analyze(document_type)
        return self._finish(insights, persist)

    def list_insights_for_document(self, document_id: uuid.UUID) -> list[Insight]:
        return self._insights.list_for_document(document_id)

    def _build_context(self, document_id: uuid.UUID) -> Optional[AnalysisContext]:
        document = self._documents.get(document_id)
        if document is None:
            return None

        extraction = self._extractions.get_latest_for_document(document_id)
        if extraction is None or extraction.status != ExtractionStatusEnum.COMPLETED:
            return None

        baseline = self._baseline_builder.build(document.document_type, exclude_document_id=document_id)
        return AnalysisContext(document=document, extraction=extraction, baseline=baseline)

    def _finish(self, insights: list[Insight], persist: bool) -> list[Insight]:
        insights = self._prioritizer.prioritize(insights)
        if self._narrative_generator is not None:
            insights = [self._narrative_generator.generate(i) for i in insights]
        if persist:
            self._insights.save_many(insights)
        return insights