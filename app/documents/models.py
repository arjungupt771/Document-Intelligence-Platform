from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from uuid import UUID


class DocumentStatus(str, Enum):
    UPLOADED = "uploaded"
    QUEUED = "queued"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class DocumentType(str, Enum):
    UNKNOWN = "unknown"
    INVOICE = "invoice"
    PURCHASE_ORDER = "purchase_order"
    CONTRACT = "contract"


@dataclass
class Document:
    id: UUID
    filename: str
    content_type: str
    size_bytes: int
    document_type: DocumentType
    status: DocumentStatus
    storage_path: str
    created_at: datetime
    updated_at: datetime