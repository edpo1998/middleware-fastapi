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

class InvoiceService:
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

    async def post(self, invoice_id: int, profile: Optional[str], idem_key: Optional[str]) -> Monitor:
        monitor = await self.repo.get(invoice_id)
        if not monitor:
            raise HTTPException(status_code=404, detail="Invoice not found")
        if monitor.status not in (MonitorStatus.draft, MonitorStatus.failed):
            raise HTTPException(status_code=409, detail=f"Cannot post from status {monitor.status}")

        monitor.status = MonitorStatus.posting
        self.session.add(monitor); 
        await self.session.commit(); 
        await self.session.refresh(monitor)
        try:
            t = registry.get("invoice", profile or "default")
            c = t.to_canonical(monitor.payload_client, ctx={"tenant": profile})
            sap_obj = t.to_sap(c, ctx={"tenant": profile})
            sap_payload = sap_obj.model_dump(by_alias=True, exclude_none=True)
            doc = self.sap.create_invoice(sap_payload, idem_key=idem_key)
            monitor.payload_sap = sap_payload
            if doc:
                monitor.sap_doc_entry = doc.get("DocEntry", None)
                monitor.sap_doc_num = doc.get("DocNum", None)
            monitor.status = MonitorStatus.posted
            await self.session.commit(); 
            await self.session.refresh(monitor)
            return monitor

        except Exception as e:
            monitor.status = MonitorStatus.failed
            monitor.error_details = {"type": e.__class__.__name__, "message": str(e)}
            await self.session.commit(); 
            await self.session.refresh(monitor)
            raise
