from dataclasses import dataclass, field

from app.documents.models import DocumentType


@dataclass(frozen=True)
class ClassificationResult:
    """Output of running a Classifier over a single document."""

    document_type: DocumentType
    confidence: float
    scores: dict[DocumentType, float] = field(default_factory=dict)
    """Normalized score for every known class considered, for debugging/audit."""

    def to_dict(self) -> dict:
        """Matches the Phase 3 output contract: {"document_type": ..., "confidence": ...}."""
        return {
            "document_type": self.document_type.value,
            "confidence": round(self.confidence, 4),
        }