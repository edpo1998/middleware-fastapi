from __future__ import annotations
from typing import Optional, Sequence
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.bootstrap_app_scheme.models import ClientKeys
from app.core.database.bootstrap_app_scheme.pydantic.client_keys_schemas import ClientKeyCreate, ClientKeyUpdate

async def ck_create(db: AsyncSession, data: ClientKeyCreate) -> ClientKeys:
    obj = ClientKeys(**data.model_dump(exclude_unset=True))
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj

async def ck_get(db: AsyncSession, cod: int) -> Optional[ClientKeys]:
    return await db.get(ClientKeys, cod)

async def ck_get_by_kid(db: AsyncSession, integration_client_cod: int, kid: str) -> Optional[ClientKeys]:
    stmt = select(ClientKeys).where(
        ClientKeys.integrationClientCod == integration_client_cod,
        ClientKeys.kid == kid,
    )
    res = await db.execute(stmt)
    return res.scalars().first()

async def ck_list_by_client(db: AsyncSession, integration_client_cod: int) -> Sequence[ClientKeys]:
    stmt = select(ClientKeys).where(ClientKeys.integrationClientCod == integration_client_cod).order_by(ClientKeys.codClientKey.desc())
    res = await db.execute(stmt)
    return res.scalars().all()

async def ck_update(db: AsyncSession, cod: int, data: ClientKeyUpdate) -> Optional[ClientKeys]:
    obj = await ck_get(db, cod)
    if not obj:
        return None
    payload = data.model_dump(exclude_unset=True)
    for k, v in payload.items():
        setattr(obj, k, v)
    await db.commit()
    await db.refresh(obj)
    return obj

async def ck_delete(db: AsyncSession, cod: int) -> bool:
    obj = await ck_get(db, cod)
    if not obj:
        return False
    await db.delete(obj)
    await db.commit()
    return True

# Helper: marcar uso (lastUsedAt)
async def ck_touch_used(db: AsyncSession, cod: int) -> bool:
    obj = await ck_get(db, cod)
    if not obj:
        return False
    obj.lastUsedAt = datetime.utcnow()
    await db.commit()
    return True
