from __future__ import annotations

from fastapi import APIRouter, Depends, Response, status

from app.api.middlewares import IdempotentRoute          
from app.core.security.hmac_auth import hmac_auth    
from app.api.deps import SessionDep                 
from app.api.schemas.invoice import ClientInvoiceCreate
from app.api.services.invoice_service import InvoiceService
from app.api.integrations.sap_b1 import SAPB1Client

router = APIRouter(route_class=IdempotentRoute)

def get_sap_client() -> SAPB1Client:
    return SAPB1Client(...)

@router.post("/invoices", dependencies=[Depends(hmac_auth)], status_code=status.HTTP_201_CREATED)
async def create_invoice(
    payload: ClientInvoiceCreate,
    response: Response,
    session: SessionDep
):
    sap = SAPB1Client("test","password","companydb","test") 
    svc = InvoiceService(session, sap)
    inv = await svc.create_draft(payload, profile=None, idem_key=None)
    _ = await svc.post( inv.id ,None, None )
    response.headers["Location"] = f"/api/v1/invoices/{inv.id}"
    return {"id": inv.id, "status": inv.status}
