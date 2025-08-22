# app/integrations/sap_b1.py
from __future__ import annotations
from typing import Dict, Any

class SAPB1Client:
    def __init__(self, base_url: str, username: str, password: str, company_db: str):
        # manejar sesión (login), cookies, etc.
        ...

    def create_invoice(self, payload: Dict[str, Any], idem_key: str | None) -> Dict[str, Any]:
        # POST a /b1s/v1/Invoices
        # Devuelve el JSON con DocEntry/DocNum.
        ...
