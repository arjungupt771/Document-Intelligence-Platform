from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Generic, TypeVar

from pydantic import BaseModel

from app.parsing.models import ParsedDocument

SchemaT = TypeVar("SchemaT", bound=BaseModel)


@dataclass
class ExtractionResult(Generic[SchemaT]):
    """
    Output of running an Extractor over a single document: a validated
    schema instance plus confidence, so downstream consumers can decide
    whether to trust a field or route it for human review.
    """

    data: SchemaT
    confidence: float
    field_confidence: dict[str, float] = field(default_factory=dict)
    """Per-field confidence in [0, 1]. A missing key means 'not attempted'."""

    def to_dict(self) -> dict:
        return {
            **self.data.model_dump(mode="json"),
            "_confidence": round(self.confidence, 4),
        }


class Extractor(ABC, Generic[SchemaT]):
    """
    Extracts a validated schema (Phase 4's Pydantic models) out of a
    ParsedDocument (Phase 2's output). One concrete Extractor per
    DocumentType -- see app/extraction/registry.py for schema selection.
    """

    @abstractmethod
    def extract(self, document: ParsedDocument) -> ExtractionResult[SchemaT]:
        raise NotImplementedError