from __future__ import annotations

import json
from datetime import datetime, UTC
from typing import Any, Dict, Optional, TypedDict

from fastapi import HTTPException, status
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database.bootstrap_app_scheme import schema_name as BOOTSTRAP_SCHEMA
from app.core.database.bootstrap_app_scheme.models import IdempotencyKeys


class IdemResult(TypedDict, total=False):
    record_id: Optional[int]
    cached: bool
    cached_status: Optional[int]
    cached_body: Optional[Dict[str, Any]]
    in_progress: bool


def _json_or_none(data: Any) -> str | None:
    if data is None:
        return None
    try:
        return json.dumps(data)
    except Exception:
        return None


async def begin_idempotency(
    session: AsyncSession,
    *,
    client_id: str,
    key: str,
    request_fingerprint: str,
) -> IdemResult:
    """
    Intenta crear registro 'processing'. Si ya existe:
      - si terminó, devuelve cached=True con respuesta
      - si sigue en curso, in_progress=True (puedes responder 409/425)
    """
    if not getattr(settings.security, "ENABLE_IDEMPOTENCY", True):
        return {"record_id": None, "cached": False, "in_progress": False}

    # 1) INSERT processing
    ins = text(f"""
        INSERT INTO {BOOTSTRAP_SCHEMA}.idempotency_keys
            (create_user, user_at, active, client_id, key, request_fingerprint, status)
        VALUES
            (0, 0, TRUE, :cid, :k, :fp, 'processing')
        ON CONFLICT (client_id, key) DO NOTHING
    """)
    res = await session.execute(ins, {"cid": client_id, "k": key, "fp": request_fingerprint})
    await session.commit()

    if res.rowcount == 1:
        # registro nuevo => devuelve el id
        row = await session.execute(
            select(IdempotencyKeys.codIdempotencyKeys).where(
                IdempotencyKeys.clientId == client_id,
                IdempotencyKeys.key == key
            ).limit(1)
        )
        rec_id = row.scalar_one()
        return {"record_id": rec_id, "cached": False, "in_progress": False}

    # 2) Ya existía: ¿terminado o en curso?
    q = await session.execute(
        select(IdempotencyKeys).where(
            IdempotencyKeys.clientId == client_id,
            IdempotencyKeys.key == key,
        ).limit(1)
    )
    row = q.scalar_one_or_none()
    if not row:
        # raro, pero evita reventar
        return {"record_id": None, "cached": False, "in_progress": False}

    if row.status != "processing" and row.httpStatus is not None:
        return {
            "record_id": row.codIdempotencyKeys,
            "cached": True,
            "cached_status": int(row.httpStatus),
            "cached_body": row.responseJson or {},
            "in_progress": False,
        }

    return {"record_id": row.codIdempotencyKeys, "cached": False, "in_progress": True}


async def finalize_idempotency(
    session: AsyncSession,
    *,
    record_id: Optional[int],
    http_status: int,
    response_obj: Dict[str, Any] | None,
) -> None:
    if not (getattr(settings.security, "ENABLE_IDEMPOTENCY", True) and record_id):
        return

    upd = text(f"""
        UPDATE {BOOTSTRAP_SCHEMA}.idempotency_keys
        SET response_json = :data::jsonb,
            http_status = :st,
            status = CASE WHEN :st BETWEEN 200 AND 299 THEN 'success' ELSE 'fail' END,
            update_date = NOW()
        WHERE cod_idempotency_keys = :id
    """)
    await session.execute(
        upd,
        {"data": _json_or_none(response_obj), "st": int(http_status), "id": int(record_id)},
    )
    await session.commit()
