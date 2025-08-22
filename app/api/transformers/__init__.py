from app.api.transformers.base import TransformerRegistry
from app.api.transformers.invoices_specs import invoice_transformer
from app.api.transformers.customer_specs import bp_transformer

registry = TransformerRegistry()
registry.register("invoice", "default", invoice_transformer)
registry.register("bp",      "default", bp_transformer)
