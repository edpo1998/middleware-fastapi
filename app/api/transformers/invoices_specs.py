from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from app.api.transformers.base import MappingSpec, FieldRule, GenericTransformer
from app.api.schemas.invoice import CanonicalInvoice, CanonicalInvoiceLine, SAPInvoice, SAPInvoiceLine
a2c = MappingSpec(
    dest_model=CanonicalInvoice,
    fields={
        "card_code": FieldRule(source="customer_code"),
        "currency":  FieldRule(source="currency"),
        "doc_date":  FieldRule(source="doc_date"),
        "lines": FieldRule(
            source="lines", many=True,
            nested=MappingSpec(
                dest_model=CanonicalInvoiceLine,
                fields={
                    "item_code":      FieldRule(source="sku"),
                    "quantity":       FieldRule(source="qty"),
                    "price":          FieldRule(source="unit_price"),
                    "warehouse_code": FieldRule(source="whs"),
                    "tax_code":       FieldRule(source="tax_code"),
                },
            ),
        ),
    },
)

c2b = MappingSpec(
    dest_model=SAPInvoice,
    fields={
        "card_code":     FieldRule(source="card_code"),
        "doc_currency":  FieldRule(source="currency"),
        "doc_date":      FieldRule(source="doc_date"),
        "document_lines": FieldRule(
            source="lines", many=True,
            nested=MappingSpec(
                dest_model=SAPInvoiceLine,
                fields={
                    "item_code":      FieldRule(source="item_code"),
                    "quantity":       FieldRule(source="quantity"),
                    "unit_price":     FieldRule(source="price"),
                    "warehouse_code": FieldRule(source="warehouse_code"),
                    "tax_code":       FieldRule(source="tax_code"),
                },
            ),
        ),
    },
)

invoice_transformer = GenericTransformer(a2c, c2b)
