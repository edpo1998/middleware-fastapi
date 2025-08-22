from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict

# A
class ClientInvoiceLine(BaseModel):
    sku: str; 
    qty: float; 
    unit_price: float
    whs: Optional[str] = None; 
    tax_code: Optional[str] = None

class ClientInvoiceCreate(BaseModel):
    customer_code: str 
    currency: str = "USD"
    doc_date: Optional[str] = None
    lines: List[ClientInvoiceLine]

# C
class CanonicalInvoiceLine(BaseModel):
    item_code: str 
    quantity: float 
    price: float
    warehouse_code: Optional[str] = None
    tax_code: Optional[str] = None

class CanonicalInvoice(BaseModel):
    card_code: str; 
    currency: str
    doc_date: Optional[str] = None
    lines: List[CanonicalInvoiceLine]

# B (SAP) + alias
class SAPInvoiceLine(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    item_code: str = Field(alias="ItemCode")
    quantity: float = Field(alias="Quantity")
    unit_price: float = Field(alias="UnitPrice")
    warehouse_code: Optional[str] = Field(default=None, alias="WarehouseCode")
    tax_code: Optional[str] = Field(default=None, alias="TaxCode")

class SAPInvoice(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    card_code: str = Field(alias="CardCode")
    card_name: Optional[str] = Field(default=None,alias="CardName")
    doc_currency: str = Field(default=None, alias="DocCurrency")
    doc_date: Optional[str] = Field(default=None, alias="DocDate")
    document_lines: List[SAPInvoiceLine] = Field(alias="DocumentLines")
