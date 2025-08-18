from __future__ import annotations
from typing import Optional, Sequence

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col

from app.core.database.bootstrap_app_scheme.models import IntegrationClients
from app.core.database.bootstrap_app_scheme.pydantic.integration_clients_schemas import (
    IntegrationClientCreate, IntegrationClientUpdate
)

async def ic_create(db: AsyncSession, data: IntegrationClientCreate) -> IntegrationClients:
    obj = IntegrationClients(**data.model_dump(exclude_unset=True))
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj

async def ic_get(db: AsyncSession, cod: int) -> Optional[IntegrationClients]:
    return await db.get(IntegrationClients, cod)

async def ic_get_by_client_id(db: AsyncSession, client_id: str) -> Optional[IntegrationClients]:
    stmt = select(IntegrationClients).where(col(IntegrationClients.clientId) == client_id)
    res = await db.execute(stmt)
    return res.scalars().first()

async def ic_list(
    db: AsyncSession, *, q: str | None = None, offset: int = 0, limit: int = 50
) -> Sequence[IntegrationClients]:
    stmt = select(IntegrationClients)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(
            col(IntegrationClients.name).ilike(like) | col(IntegrationClients.clientId).ilike(like)
        )
    stmt = stmt.order_by(col(IntegrationClients.codIntegrationClient).desc()).offset(offset).limit(limit)
    res = await db.execute(stmt)
    return res.scalars().all()

async def ic_count(db: AsyncSession, *, q: str | None = None) -> int:
    stmt = select(func.count(IntegrationClients.codIntegrationClient))
    if q:
        like = f"%{q}%"
        stmt = stmt.where(
            col(IntegrationClients.name).ilike(like) | col(IntegrationClients.clientId).ilike(like)
        )
    res = await db.execute(stmt)
    return int(res.scalar_one())

async def ic_update(db: AsyncSession, cod: int, data: IntegrationClientUpdate) -> Optional[IntegrationClients]:
    obj = await ic_get(db, cod)
    if not obj:
        return None
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    await db.commit()
    await db.refresh(obj)
    return obj

async def ic_delete(db: AsyncSession, cod: int) -> bool:
    obj = await ic_get(db, cod)
    if not obj:
        return False
    await db.delete(obj)
    await db.commit()
    return True
