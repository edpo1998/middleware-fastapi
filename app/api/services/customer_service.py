# app/services/invoice_service.py
from __future__ import annotations
from typing import Optional
from fastapi import HTTPException, status
from sqlmodel import Session
from app.core.database.mcs_scheme.models.monitor import Monitor , MonitorStatus
from app.api.schemas.invoice import ClientInvoiceCreate

from app.api.repositories.invoice_repository import InvoiceRepository
from app.api.integrations.sap_b1 import SAPB1Client 

from app.api.transformers import registry


class CustomerService:
    def __init__(self, session: Session, sap: SAPB1Client):
        self.session = session
        self.repo = InvoiceRepository(session)
        self.sap = sap

    async def create_draft(self, payload: ClientInvoiceCreate, profile: Optional[str], idem_key: Optional[str]) -> Monitor:
        inv = Monitor(status=MonitorStatus.draft,document=1, payload_client=payload.model_dump())
        self.session.add(inv)
        await self.session.flush()
        await self.session.commit()
        await self.session.refresh(inv)

        return inv

    def post(self, invoice_id: int, profile: Optional[str], idem_key: Optional[str]) -> Monitor:
        inv = self.repo.get(invoice_id)
        if not inv:
            raise HTTPException(status_code=404, detail="Invoice not found")
        if inv.status not in (MonitorStatus.draft, MonitorStatus.failed):
            raise HTTPException(status_code=409, detail=f"Cannot post from status {inv.status}")

        inv.status = MonitorStatus.posting
        self.session.add(inv); self.session.commit(); self.session.refresh(inv)

        try:
            # A -> C
            transformer = get_invoice_transformer(profile)
            a = ClientInvoiceCreate.model_validate(inv.payload_client)
            c = transformer.to_canonical(a)
            # C -> B
            sap_obj = transformer.to_sap(c)
            sap_payload = sap_obj.model_dump(by_alias=True, exclude_none=True)

            # Llamada a SAP B1
            doc = self.sap.create_invoice(sap_payload, idem_key=idem_key)
            # doc puede devolver DocEntry/DocNum (ajusta al wrapper)
            inv.payload_sap = sap_payload
            inv.sap_doc_entry = doc.get("DocEntry")
            inv.sap_doc_num = doc.get("DocNum")
            inv.status = MonitorStatus.posted
            self.session.commit(); self.session.refresh(inv)
            return inv

        except Exception as e:
            inv.status = MonitorStatus.failed
            inv.error_details = {"type": e.__class__.__name__, "message": str(e)}
            self.session.commit(); self.session.refresh(inv)
            raise
