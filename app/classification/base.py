from abc import ABC, abstractmethod

from app.classification.models import ClassificationResult
from app.parsing.models import ParsedDocument


class Classifier(ABC):
    """
    Classifies a ParsedDocument into one of the known DocumentTypes.

    Rule-based, traditional-ML, embedding, and LLM classifiers all
    implement this same interface, so they can be swapped in and
    benchmarked against each other (see app/classification/metrics.py)
    without touching any caller.
    """

    @abstractmethod
    def classify(self, document: ParsedDocument) -> ClassificationResult:
        raise NotImplementedError