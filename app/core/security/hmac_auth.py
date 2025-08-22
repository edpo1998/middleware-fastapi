from __future__ import annotations

import base64
import hashlib
import hmac
import ipaddress
import time
from datetime import datetime, UTC
from typing import Any, Dict, Optional

from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import async_session
from app.core.database.bootstrap_app_scheme import schema_name as BOOTSTRAP_SCHEMA
from app.core.database.bootstrap_app_scheme.models import (
    IntegrationClients,
    ClientKeys,
    ClientIPs,
    SecurityNonces,
)


# -------- helpers --------

def _sha256_hex(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def _hmac_b64(secret: str, msg: str) -> str:
    dig = hmac.new(secret.encode(), msg.encode(), hashlib.sha256).digest()
    return base64.urlsafe_b64encode(dig).decode().rstrip("=")

def _client_ip(request: Request) -> str:
    if getattr(settings.security, "TRUST_PROXY_HEADERS", False):
        xfwd = request.headers.get("x-forwarded-for")
        if xfwd:
            return xfwd.split(",")[0].strip()
    return request.client.host if request.client else "0.0.0.0"

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
    # misma forma que tenías (no cambié el layout)
    return "\n".join([method, path, query, cid, kid, ts, nonce, body_hash])

async def _get_session() -> AsyncSession:
    async with async_session() as s:  # type: ignore
        yield s


# -------- dependencia principal --------

async def hmac_auth(
    request: Request,
    session: AsyncSession = Depends(_get_session),
    x_client_id: str = Header(..., alias="X-Client-Id"),
    x_key_id: str = Header(..., alias="X-Key-Id"),
    x_timestamp: Optional[str] = Header(None, alias="X-Timestamp"),
    x_nonce: Optional[str] = Header(None, alias="X-Nonce"),
    x_signature: str = Header(..., alias="X-Signature"),
) -> Dict[str, Any]:
    # 0) Toggle global
    if not getattr(settings.security, "ENABLE_HMAC", True):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="HMAC disabled")

    # 1) Cliente activo
    res_client = await session.execute(
        select(IntegrationClients).where(
            IntegrationClients.clientId == x_client_id,
            IntegrationClients.active.is_(True),
        ).limit(1)
    )
    client = res_client.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="unknown client")

    # 2) IP contra CIDRs (si tiene reglas)
    ip = _client_ip(request)
    res_cidrs = await session.execute(
        select(ClientIPs.cidr).where(ClientIPs.integrationClientCod == client.codIntegrationClient)
    )
    cidrs = [row[0] for row in res_cidrs.all()]
    if cidrs and not _ip_allowed(ip, cidrs):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="ip not allowed")

    # 3) Timestamp (si habilitado)
    must_check_ts = getattr(settings.security, "ENABLE_TIMESTAMP", True)
    if must_check_ts:
        if not x_timestamp:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing timestamp")
        try:
            ts = int(x_timestamp)
        except (TypeError, ValueError):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="bad timestamp")
        window = int(getattr(settings.security, "HMAC_WINDOW_SECONDS", 300))
        skew = int(getattr(settings.security, "CLOCK_SKEW_SECONDS", 60))
        now = int(time.time())
        if ts < now - (window + skew) or ts > now + skew:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="timestamp expired")

    # 4) Nonce anti-replay (si habilitado)
    if getattr(settings.security, "ENABLE_NONCE", True):
        if not x_nonce:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing nonce")
        # ON CONFLICT DO NOTHING sobre (client_id, nonce)
        stmt_nonce = text(f"""
            INSERT INTO {BOOTSTRAP_SCHEMA}.security_nonces
                (integration_client_cod, create_user, user_at, active, client_id, nonce, request_ts, received_at)
            VALUES
                (:ic, 0, 0, TRUE, :cid, :nonce, to_timestamp(:ts), NOW())
            ON CONFLICT (client_id, nonce) DO NOTHING
        """)
        res = await session.execute(
            stmt_nonce,
            {
                "ic": client.codIntegrationClient,
                "cid": x_client_id,
                "nonce": x_nonce,
                "ts": int(x_timestamp) if x_timestamp else int(time.time()),
            },
        )
        await session.commit()
        if res.rowcount == 0:
            # Nonce ya existe
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="replay detected")

    # 5) Key activa por kid (y no expirada)
    res_key = await session.execute(
        select(ClientKeys).where(
            ClientKeys.integrationClientCod == client.codIntegrationClient,
            ClientKeys.kid == x_key_id,
            ClientKeys.active.is_(True),
            (ClientKeys.expiresAt.is_(None)) | (ClientKeys.expiresAt > func.now()),
        ).limit(1)
    )
    key = res_key.scalar_one_or_none()
    if not key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="key not found or inactive/expired")

    # 6) Firma HMAC
    # lee y reinyecta body para que el endpoint pueda usarlo
    body = await request.body()
    async def _receive():
        return {"type": "http.request", "body": body, "more_body": False}
    request._receive = _receive
    request.state.raw_body = body

    method = request.method.upper()
    path = request.url.path
    query = request.url.query or ""   # usa exactamente la query como viene
    body_hash = _sha256_hex(body)

    ts_for_sig = x_timestamp or "" if must_check_ts else ""
    nonce_for_sig = x_nonce or "" if getattr(settings.security, "ENABLE_NONCE", True) else ""

    # MISMA cadena que usabas:
    signing_string = _canonical_v1(method, path, query, x_client_id, x_key_id, ts_for_sig, nonce_for_sig, body_hash)
    expected_sig = _hmac_b64(key.secret, signing_string)
    # print("HOLA")
    # print(signing_string)
    print(expected_sig) 
    print(x_signature)
    if not hmac.compare_digest(expected_sig, x_signature or ""):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid signature")

    # 7) last_used_at
    await session.execute(
        text(f"UPDATE {BOOTSTRAP_SCHEMA}.client_keys SET last_used_at = NOW() WHERE cod_client_key = :i"),
        {"i": key.codClientKey},
    )
    await session.commit()

    # retorno útil para tu endpoint si lo necesita
    return {
        "client_id": x_client_id,
        "kid": x_key_id,
        "integration_client_cod": client.codIntegrationClient,
        "ip": ip,
        "body": body,
    }
