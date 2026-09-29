from dataclasses import dataclass
from enum import Enum


class QueryType(str, Enum):
    STRUCTURED = "structured"
    SEMANTIC = "semantic"
    CROSS_DOCUMENT = "cross_document"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class QueryRequest:
    query: str


@dataclass(frozen=True)
class QueryRoute:
    query: str
    query_type: QueryType

@dataclass(frozen=True)
class CrossDocumentRoute:
    query: str
    query_type: QueryType = QueryType.CROSS_DOCUMENT