import re
from collections import defaultdict
from typing import Optional

from app.classification.base import Classifier
from app.classification.models import ClassificationResult
from app.documents.models import DocumentType
from app.parsing.models import ParsedDocument

# Keyword/phrase signals per document type. Matching is case-insensitive.
# Weights are hand-tuned by how distinctive a phrase is (e.g. "purchase
# order" is a near-certain signal; "vendor" is only weak support).
_KEYWORD_WEIGHTS: dict[DocumentType, dict[str, float]] = {
    DocumentType.INVOICE: {
        r"\binvoice\b": 3.0,
        r"\binvoice\s*(no|number|#)\b": 4.0,
        r"\bbill\s*to\b": 2.0,
        r"\bamount\s*due\b": 2.0,
        r"\bdue\s*date\b": 1.5,
        r"\bsubtotal\b": 1.5,
        r"\btax\b": 1.0,
        r"\bremit\s*to\b": 2.0,
    },
    DocumentType.PURCHASE_ORDER: {
        r"\bpurchase\s*order\b": 4.0,
        r"\bp\.?o\.?\s*(no|number|#)\b": 4.0,
        r"\bbuyer\b": 1.5,
        r"\bsupplier\b": 1.5,
        r"\bship\s*to\b": 2.0,
        r"\border\s*date\b": 1.5,
        r"\bvendor\b": 1.0,
    },
    DocumentType.CONTRACT: {
        r"\bagreement\b": 2.5,
        r"\bcontract\b": 3.0,
        r"\bparties\b": 1.5,
        r"\bwhereas\b": 3.0,
        r"\btermination\b": 2.0,
        r"\beffective\s*date\b": 2.0,
        r"\bindemnif\w*\b": 2.5,
        r"\bgoverning\s*law\b": 2.0,
        r"\bconfidentiality\b": 1.5,
    },
}

_DEFAULT_MIN_CONFIDENCE = 0.4
"""Below this, we report UNKNOWN rather than force a guess."""

_MAX_MATCHES_PER_PATTERN = 3
"""Caps how much a single repeated phrase can dominate the score."""


class RuleBasedClassifier(Classifier):
    """
    Keyword/regex scoring baseline for document classification.

    Deliberately simple and fully explainable: every score can be traced
    back to the phrases that produced it. This is the bar that
    traditional-ML, embedding, and LLM classifiers need to clear before
    we adopt something more expensive -- per the "don't jump straight to
    an LLM" decision.
    """

    def __init__(
        self,
        keyword_weights: Optional[dict[DocumentType, dict[str, float]]] = None,
        min_confidence: float = _DEFAULT_MIN_CONFIDENCE,
    ):
        weights = keyword_weights or _KEYWORD_WEIGHTS
        self._compiled: dict[DocumentType, list[tuple[re.Pattern, float]]] = {
            document_type: [
                (re.compile(pattern, re.IGNORECASE), weight)
                for pattern, weight in patterns.items()
            ]
            for document_type, patterns in weights.items()
        }
        self._min_confidence = min_confidence

    def classify(self, document: ParsedDocument) -> ClassificationResult:
        text = document.text
        raw_scores = self._score(text)

        total = sum(raw_scores.values())
        known_types = list(self._compiled.keys())

        if total == 0:
            return ClassificationResult(
                document_type=DocumentType.UNKNOWN,
                confidence=1.0,
                scores={document_type: 0.0 for document_type in known_types},
            )

        normalized_scores = {
            document_type: raw_scores.get(document_type, 0.0) / total
            for document_type in known_types
        }

        best_type = max(normalized_scores, key=normalized_scores.get)
        best_score = normalized_scores[best_type]

        if best_score < self._min_confidence:
            return ClassificationResult(
                document_type=DocumentType.UNKNOWN,
                confidence=round(1.0 - best_score, 4),
                scores=normalized_scores,
            )

        return ClassificationResult(
            document_type=best_type,
            confidence=best_score,
            scores=normalized_scores,
        )

    def _score(self, text: str) -> dict[DocumentType, float]:
        scores: dict[DocumentType, float] = defaultdict(float)

        for document_type, patterns in self._compiled.items():
            for pattern, weight in patterns:
                match_count = len(pattern.findall(text))
                if match_count:
                    scores[document_type] += weight * min(match_count, _MAX_MATCHES_PER_PATTERN)

        return scores