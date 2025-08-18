import hashlib
from datetime import datetime, UTC
from typing import Any, Dict, Optional

from fastapi import HTTPException, Header
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_409_CONFLICT
from sqlmodel import Session, select

from app.core.config import settings
from app.core.database.bootstrap_app_scheme.models import IdempotencyKeys


def _fingerprint(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def get_idempotency_key(idem_key: Optional[str] = Header(None, alias="Idempotency-Key")) -> Optional[str]:
    # Dependencia separada por si quieres documentarlo en OpenAPI
    return idem_key


def begin_idempotency(session: Session, client_id: str, idem_key: Optional[str], body: bytes):
    if not settings.security.ENABLE_IDEMPOTENCY:
        return None

    if settings.security.IDEMPOTENCY_REQUIRED and not idem_key:
        raise HTTPException(HTTP_400_BAD_REQUEST, "Idempotency-Key required")

    if not idem_key:
        return None

    fp = _fingerprint(body)
    rec = session.exec(
        select(IdempotencyKeys).where(
            IdempotencyKeys.clientId == client_id,
            IdempotencyKeys.key == idem_key
        )
    ).first()

    if rec:
        if rec.requestFingerprint != fp:
            raise HTTPException(HTTP_409_CONFLICT, "idempotency key reused with different body")
        # respuesta cacheada
        if rec.responseJson is not None and rec.httpStatus is not None:
            return {"replay": True, "status": rec.httpStatus, "body": rec.responseJson}
        # en procesamiento o sin respuesta aún
        return {"replay": False, "record_id": rec.codIdempotencyKeys, "fp": fp}

    new_rec = IdempotencyKeys(
        clientId=client_id,
        key=idem_key,
        requestFingerprint=fp,
        responseJson=None,
        httpStatus=None,
        status="processing",
    )
    session.add(new_rec)
    session.commit()
    session.refresh(new_rec)
    return {"replay": False, "record_id": new_rec.codIdempotencyKeys, "fp": fp}


def finalize_idempotency(session: Session, record_id: Optional[int], http_status: int, response_obj: Dict[str, Any]):
    if not (settings.security.ENABLE_IDEMPOTENCY and record_id):
        return
    rec = session.get(IdempotencyKeys, record_id)
    if not rec:
        return
    rec.httpStatus = http_status
    rec.responseJson = response_obj
    rec.status = "success" if 200 <= http_status < 300 else "fail"
    rec.updateDate = datetime.now(UTC).replace(tzinfo=None)
    session.add(rec)
    session.commit()
