from __future__ import annotations

import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class DriftDimension(str, Enum):
    DOCUMENT_TYPE_DISTRIBUTION = "document_type_distribution"
    FIELD_PRESENCE = "field_presence"
    NUMERIC_VALUE = "numeric_value"
    EMBEDDING = "embedding"
    SCHEMA = "schema"
    EXTRACTION_QUALITY = "extraction_quality"
    RETRIEVAL_QUALITY = "retrieval_quality"


class DriftSeverity(str, Enum):
    NONE = "none"
    MODERATE = "moderate"
    SIGNIFICANT = "significant"


@dataclass(frozen=True)
class DriftThresholds:
    """
    Same PSI-style scale applied to every drift dimension in this module,
    including the two that aren't PSI itself (extraction-quality and
    retrieval-quality use a direct 0..1 score) -- one alerting story
    instead of a different threshold set per dimension. (15.10)
    """

    moderate: float = 0.1
    significant: float = 0.25

    def classify(self, score: float) -> DriftSeverity:
        if score >= self.significant:
            return DriftSeverity.SIGNIFICANT
        if score >= self.moderate:
            return DriftSeverity.MODERATE
        return DriftSeverity.NONE

    @classmethod
    def from_env(cls) -> "DriftThresholds":
        return cls(
            moderate=float(os.getenv("DRIFT_THRESHOLD_MODERATE", "0.1")),
            significant=float(os.getenv("DRIFT_THRESHOLD_SIGNIFICANT", "0.25")),
        )


@dataclass
class BaselineSnapshot:
    """What gets persisted as the reference distribution for one document type. (15.2)"""

    document_type_distribution: dict[str, float]
    field_presence_rates: dict[str, float]
    numeric_field_bins: dict[str, dict]
    """{field_name: {"edges": [...], "distribution": {bucket_label: proportion}}}"""
    schema_keys: list[str]
    mean_extraction_confidence: Optional[float]
    sample_size: int
    embedding_centroid: Optional[list[float]] = None
    retrieval_hit_rate: Optional[float] = None
    retrieval_mrr: Optional[float] = None


@dataclass
class DriftResult:
    dimension: DriftDimension
    key: str
    """What within the dimension this measures -- a field name, 'document_type', 'hit_rate_at_k', etc."""
    score: float
    severity: DriftSeverity
    baseline_summary: dict
    current_summary: dict
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    detected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))