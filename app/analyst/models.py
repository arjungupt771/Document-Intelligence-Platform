from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from app.documents.models import Document
from app.storage.models import ExtractionORM


class InsightType(str, Enum):
    COMPLETENESS = "completeness"
    FINANCIAL = "financial"
    ANOMALY = "anomaly"
    RISK = "risk"
    CROSS_DOCUMENT = "cross_document"
    TREND = "trend"


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


SEVERITY_WEIGHT: dict[Severity, int] = {
    Severity.LOW: 1,
    Severity.MEDIUM: 2,
    Severity.HIGH: 3,
    Severity.CRITICAL: 4,
}


@dataclass(frozen=True)
class InsightEvidence:
    """
    Provenance for one insight -- always traceable to one extraction
    attempt on one document, optionally down to a field or page. This is
    the unit both the API and the narrative-verification step consume.
    """

    document_id: str
    document_type: str
    text: str
    field_path: Optional[str] = None
    page_number: Optional[int] = None
    extraction_id: Optional[str] = None


@dataclass
class Insight:
    type: InsightType
    severity: Severity
    title: str
    description: str
    confidence: float
    evidence: list[InsightEvidence] = field(default_factory=list)
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    document_ids: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    priority_score: Optional[float] = None
    narrative: Optional[str] = None
    narrative_verified: Optional[bool] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.document_ids:
            self.document_ids = list(dict.fromkeys(e.document_id for e in self.evidence))


@dataclass
class BaselineStats:
    """Historical distribution of one numeric field, scoped to a document type."""

    mean: float
    stdev: float
    sample_size: int

    def z_score(self, value: float) -> Optional[float]:
        if self.sample_size < 3 or self.stdev == 0:
            return None
        return (value - self.mean) / self.stdev


@dataclass
class AnalysisContext:
    """Input bundle handed to every single-document Analyzer."""

    document: Document
    extraction: ExtractionORM
    baseline: Optional[BaselineStats] = None


@dataclass
class AnalystReport:
    document_id: str
    insights: list[Insight] = field(default_factory=list)
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))