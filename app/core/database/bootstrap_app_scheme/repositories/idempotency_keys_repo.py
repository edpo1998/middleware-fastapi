from __future__ import annotations
from typing import Optional
from datetime import datetime, timedelta

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.bootstrap_app_scheme.models import IdempotencyKeys
from app.core.database.bootstrap_app_scheme.pydantic.idempotency_keys_schemas import (
    IdempotencyKeyCreate, IdempotencyKeyUpdate
)

# Reclama / crea un registro para (clientId, key). Devuelve el registro "processing" existente o uno nuevo.
async def idem_claim(db: AsyncSession, data: IdempotencyKeyCreate) -> IdempotencyKeys:
    stmt = select(IdempotencyKeys).where(
        IdempotencyKeys.clientId == data.clientId,
        IdempotencyKeys.key == data.key,
    )
    res = await db.execute(stmt)
    obj = res.scalars().first()
    if obj:
        return obj
    obj = IdempotencyKeys(**data.model_dump(exclude_unset=True))
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj

async def idem_get(db: AsyncSession, client_id: str, key: str) -> Optional[IdempotencyKeys]:
    stmt = select(IdempotencyKeys).where(
        IdempotencyKeys.clientId == client_id,
        IdempotencyKeys.key == key,
    )
    res = await db.execute(stmt)
    return res.scalars().first()

# Marca como completado con respuesta y httpStatus
async def idem_complete(
    db: AsyncSession,
    client_id: str,
    key: str,
    response_json: dict,
    http_status: int,
    *,
    status: str = "completed",
) -> bool:
    obj = await idem_get(db, client_id, key)
    if not obj:
        return False
    obj.responseJson = response_json
    obj.httpStatus = http_status
    obj.status = status
    await db.commit()
    return True

# Actualiza solo el status si lo necesitas
async def idem_touch_status(db: AsyncSession, client_id: str, key: str, status: str) -> bool:
    obj = await idem_get(db, client_id, key)
    if not obj:
        return False
    obj.status = status
    await db.commit()
    return True

# Existe (cualquier estado)
async def idem_exists(db: AsyncSession, client_id: str, key: str) -> bool:
    return (await idem_get(db, client_id, key)) is not None

# Limpia registros viejos opcionalmente
async def idem_prune_old(db: AsyncSession, older_than_days: int = 30) -> int:
    cutoff = datetime.utcnow() - timedelta(days=older_than_days)
    stmt = delete(IdempotencyKeys).where(IdempotencyKeys.createDate < cutoff)
    res = await db.execute(stmt)
    await db.commit()
    return res.rowcount or 0
