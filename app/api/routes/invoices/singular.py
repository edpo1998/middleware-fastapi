from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlmodel import Session

from app.core.security.hmac_auth import hmac_auth
from app.core.security.idempotency import begin_idempotency, finalize_idempotency, get_idempotency_key
from app.core.database.db import get_session

router = APIRouter()

@router.post("/invoices")
async def create_invoice(
    request: Request,
    session: Session = Depends(get_session),
    auth = Depends(hmac_auth),
    idem_key: str | None = Depends(get_idempotency_key),
):
    body: bytes = auth["body"]  # ya lo leyó hmac_auth; evita .body() doble

    idem = begin_idempotency(session, auth["client_id"], idem_key, body)
    if isinstance(idem, dict) and idem.get("replay"):
        return JSONResponse(status_code=idem["status"], content=idem["body"])

    # TODO: valida/transforma -> llama SAP B1 (Service Layer) -> construye respuesta
    response_payload = {
        "status": "received",
        "client": auth["client_id"],
        "echo": "invoice accepted for processing"
    }
    status_code = 200

    finalize_idempotency(session, idem and idem.get("record_id"), status_code, response_payload)
    return JSONResponse(status_code=status_code, content=response_payload)
