from __future__ import annotations
from typing import Optional
from datetime import datetime, timedelta

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.bootstrap_app_scheme.models import SecurityNonces
from app.core.database.bootstrap_app_scheme.pydantic.security_nonces_schemas import SecurityNonceCreate

# Registra un nonce (único por clientId + nonce)
async def nonce_register(db: AsyncSession, data: SecurityNonceCreate) -> SecurityNonces:
    obj = SecurityNonces(**data.model_dump(exclude_unset=True))
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj

# ¿Existe (clientId, nonce)? para prevenir replay
async def nonce_exists(db: AsyncSession, client_id: str, nonce: str) -> bool:
    stmt = select(SecurityNonces).where(
        SecurityNonces.clientId == client_id,
        SecurityNonces.nonce == nonce,
    )
    res = await db.execute(stmt)
    return res.scalars().first() is not None

async def nonce_get(db: AsyncSession, cod: int) -> Optional[SecurityNonces]:
    return await db.get(SecurityNonces, cod)

# Limpieza por antigüedad (por ejemplo, > 1 día)
async def nonce_prune_old(db: AsyncSession, older_than_hours: int = 24) -> int:
    cutoff = datetime.utcnow() - timedelta(hours=older_than_hours)
    stmt = delete(SecurityNonces).where(SecurityNonces.createDate < cutoff)
    res = await db.execute(stmt)
    await db.commit()
    return res.rowcount or 0
