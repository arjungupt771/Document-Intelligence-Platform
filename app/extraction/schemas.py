from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class LineItem(BaseModel):
    description: str
    quantity: Optional[Decimal] = None
    unit_price: Optional[Decimal] = None
    total: Optional[Decimal] = None


class InvoiceSchema(BaseModel):
    vendor: Optional[str] = None
    invoice_number: Optional[str] = None
    invoice_date: Optional[date] = None
    due_date: Optional[date] = None
    currency: Optional[str] = None
    subtotal: Optional[Decimal] = None
    tax: Optional[Decimal] = None
    total: Optional[Decimal] = None
    line_items: list[LineItem] = Field(default_factory=list)


class PurchaseOrderItem(BaseModel):
    description: str
    quantity: Optional[Decimal] = None
    unit_price: Optional[Decimal] = None
    total: Optional[Decimal] = None


class PurchaseOrderSchema(BaseModel):
    buyer: Optional[str] = None
    supplier: Optional[str] = None
    po_number: Optional[str] = None
    order_date: Optional[date] = None
    items: list[PurchaseOrderItem] = Field(default_factory=list)
    currency: Optional[str] = None
    total: Optional[Decimal] = None


class ContractSchema(BaseModel):
    parties: list[str] = Field(default_factory=list)
    effective_date: Optional[date] = None
    termination_date: Optional[date] = None
    payment_terms: Optional[str] = None
    renewal_terms: Optional[str] = None
    obligations: list[str] = Field(default_factory=list)
    clauses: list[str] = Field(default_factory=list)