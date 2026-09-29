from typing import Optional

from app.documents.models import DocumentType
from app.extraction.base import Extractor
from app.extraction.contract_extractor import ContractExtractor
from app.extraction.errors import UnsupportedDocumentTypeError
from app.extraction.invoice_extractor import InvoiceExtractor
from app.extraction.purchase_order_extractor import PurchaseOrderExtractor
from app.extraction.schemas import ContractSchema, InvoiceSchema, PurchaseOrderSchema

# Which Pydantic schema applies to each classified document type. This is
# the "schema selection" step of the pipeline: DocumentType -> schema.
SCHEMA_BY_DOCUMENT_TYPE = {
    DocumentType.INVOICE: InvoiceSchema,
    DocumentType.PURCHASE_ORDER: PurchaseOrderSchema,
    DocumentType.CONTRACT: ContractSchema,
}


class ExtractorRegistry:
    """Resolves the right Extractor for a classified DocumentType."""

    def __init__(self, extractors: Optional[dict[DocumentType, Extractor]] = None):
        self._extractors = extractors if extractors is not None else self._default_extractors()

    def get_extractor(self, document_type: DocumentType) -> Extractor:
        extractor = self._extractors.get(document_type)
        if extractor is None:
            raise UnsupportedDocumentTypeError(document_type)
        return extractor

    @staticmethod
    def _default_extractors() -> dict[DocumentType, Extractor]:
        return {
            DocumentType.INVOICE: InvoiceExtractor(),
            DocumentType.PURCHASE_ORDER: PurchaseOrderExtractor(),
            DocumentType.CONTRACT: ContractExtractor(),
        }


default_extractor_registry = ExtractorRegistry()