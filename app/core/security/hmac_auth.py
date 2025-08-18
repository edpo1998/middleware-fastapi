import base64, hashlib, hmac, ipaddress, time
from datetime import datetime, UTC
from typing import Any, Dict, Optional

from fastapi import Header, HTTPException, Request, Depends
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN
from sqlmodel import Session, select

from app.core.config import settings
from app.core.database.db_sync import get_session
from app.core.database.bootstrap_app_scheme.models import (
    IntegrationClients, ClientKeys, ClientIPs, SecurityNonces
)


def _sha256_hex(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def _hmac_b64(secret: str, msg: str) -> str:
    dig = hmac.new(secret.encode(), msg.encode(), hashlib.sha256).digest()
    return base64.urlsafe_b64encode(dig).decode().rstrip("=")

def _client_ip(request: Request) -> str:
    if settings.security.TRUST_PROXY_HEADERS:
        xfwd = request.headers.get("x-forwarded-for")
        if xfwd:
            return xfwd.split(",")[0].strip()
    # request.client puede ser None en algunos test runners
    return (request.client.host if request.client else "0.0.0.0")

def _ip_allowed(ip: str, cidrs: list[str]) -> bool:
    ip_obj = ipaddress.ip_address(ip)
    for c in cidrs:
        try:
            if ip_obj in ipaddress.ip_network(c, strict=False):
                return True
        except ValueError:
            continue
    return False

def _canonical_v1(method: str, path: str, query: str, cid: str, kid: str, ts: str, nonce: str, body_hash: str) -> str:
    return "\n".join([method, path, query, cid, kid, ts, nonce, body_hash])


async def hmac_auth(
    request: Request,
    session: Session = Depends(get_session),
    x_client_id: str = Header(..., alias="X-Client-Id"),
    x_key_id: str = Header(..., alias="X-Key-Id"),
    x_timestamp: Optional[str] = Header(None, alias="X-Timestamp"),
    x_nonce: Optional[str] = Header(None, alias="X-Nonce"),
    x_signature: str = Header(..., alias="X-Signature"),
) -> Dict[str, Any]:
    # 0) Toggle global HMAC
    if not settings.security.ENABLE_HMAC:
        # En local puedes permitir paso sin validar:
        # return {"client_id": x_client_id, "kid": x_key_id, "integration_client_cod": None, "ip": _client_ip(request), "body": await request.body()}
        raise HTTPException(HTTP_401_UNAUTHORIZED, "HMAC disabled")

    # 1) Cliente + llave
    client = session.exec(
        select(IntegrationClients).where(
            IntegrationClients.clientId == x_client_id,
            IntegrationClients.active == True,  # noqa
        )
    ).first()
    if not client:
        raise HTTPException(HTTP_401_UNAUTHORIZED, "unknown client")

    key = session.exec(
        select(ClientKeys).where(
            ClientKeys.integrationClientCod == client.codIntegrationClient,
            ClientKeys.kid == x_key_id,
            ClientKeys.active == True,  # noqa
        )
    ).first()
    if not key:
        raise HTTPException(HTTP_401_UNAUTHORIZED, "unknown key")

    # 2) IP allowlist
    # Trae objetos completos y mapea .cidr (evita filas tuple/Row)
    ip_rows = session.exec(
        select(ClientIPs).where(
            ClientIPs.integrationClientCod == client.codIntegrationClient,
            ClientIPs.active == True,  # noqa
        )
    ).all()
    cidrs = [r.cidr for r in ip_rows]
    ip = _client_ip(request)
    if cidrs and not _ip_allowed(ip, cidrs):
        raise HTTPException(HTTP_403_FORBIDDEN, f"ip {ip} not allowed")

    # 3) Timestamp (condicional)
    must_check_ts = (
        settings.security.ENABLE_TIMESTAMP and
        (not settings.security.REQUIRE_TIMESTAMP_WITH_NONCE or settings.security.ENABLE_NONCE)
    )
    if must_check_ts:
        if not x_timestamp:
            raise HTTPException(HTTP_401_UNAUTHORIZED, "missing timestamp")
        try:
            ts = int(x_timestamp)
        except ValueError:
            raise HTTPException(HTTP_401_UNAUTHORIZED, "bad timestamp")
        now = int(time.time())
        if abs(now - ts) > settings.security.HMAC_WINDOW_SECONDS:
            raise HTTPException(HTTP_401_UNAUTHORIZED, "timestamp expired")

    # 4) Firma HMAC (usa cadena vacía si faltan ts/nonce)
    raw_body: bytes
    if hasattr(request.state, "raw_body"):
        raw_body = request.state.raw_body  # reusar si otro dep ya lo leyó
    else:
        raw_body = await request.body()
        request.state.raw_body = raw_body  # cachear para el endpoint

    method = request.method.upper()
    path = request.url.path
    query = request.url.query or ""  # cuidado: debe coincidir EXACTO con lo que firmó el cliente
    bhash = _sha256_hex(raw_body)
    ts_for_sig = x_timestamp or ""
    nonce_for_sig = x_nonce or ""
    canonical = _canonical_v1(method, path, query, x_client_id, x_key_id, ts_for_sig, nonce_for_sig, bhash)
    expected = _hmac_b64(key.secret, canonical)
    if not hmac.compare_digest(expected, x_signature):
        raise HTTPException(HTTP_401_UNAUTHORIZED, "invalid signature")

    # 5) Nonce (solo si está habilitado)
    if settings.security.ENABLE_NONCE:
        if not x_nonce:
            raise HTTPException(HTTP_401_UNAUTHORIZED, "missing nonce")
        try:
            session.add(SecurityNonces(
                integrationClientCod=client.codIntegrationClient,
                clientId=x_client_id,
                nonce=x_nonce,
                requestTs=datetime.utcfromtimestamp(int(x_timestamp)) if x_timestamp else datetime.now(UTC).replace(tzinfo=None),
                receivedAt= datetime.now(UTC).replace(tzinfo=None)if hasattr(SecurityNonces, "receivedAt") else None,  # si tu modelo lo tiene
            ))
            key.lastUsedAt =  datetime.now(UTC).replace(tzinfo=None)
            session.commit()
        except Exception:
            session.rollback()
            raise HTTPException(HTTP_401_UNAUTHORIZED, "replay detected")

    return {
        "client_id": x_client_id,
        "kid": x_key_id,
        "integration_client_cod": client.codIntegrationClient,
        "ip": ip,
        "body": raw_body,
    }
