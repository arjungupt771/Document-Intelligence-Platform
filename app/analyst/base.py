from abc import ABC, abstractmethod

from app.analyst.models import AnalysisContext, Insight


class Analyzer(ABC):
    """One rule family applied to a single document's latest extraction."""

    @abstractmethod
    def analyze(self, context: AnalysisContext) -> list[Insight]:
        raise NotImplementedError


class ComparativeAnalyzer(ABC):
    """Applied to a pair of documents (e.g. invoice vs. purchase order)."""

    @abstractmethod
    def compare(self, context_a: AnalysisContext, context_b: AnalysisContext) -> list[Insight]:
        raise NotImplementedError