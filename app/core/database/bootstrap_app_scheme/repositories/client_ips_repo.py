from __future__ import annotations
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.bootstrap_app_scheme.models import ClientIPs
from app.core.database.bootstrap_app_scheme.pydantic.client_ips_schemas import ClientIpCreate, ClientIpUpdate

async def ip_create(db: AsyncSession, data: ClientIpCreate) -> ClientIPs:
    obj = ClientIPs(**data.model_dump(exclude_unset=True))
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj

async def ip_upsert(db: AsyncSession, data: ClientIpCreate) -> ClientIPs:
    """
    Inserta si no existe (integrationClientCod, cidr); si existe, actualiza active/createUser/userAt.
    """
    stmt = select(ClientIPs).where(
        ClientIPs.integrationClientCod == data.integrationClientCod,
        ClientIPs.cidr == data.cidr,
    )
    res = await db.execute(stmt)
    obj = res.scalars().first()
    if obj:
        obj.active = data.active
        obj.createUser = data.createUser
        obj.userAt = data.userAt
        await db.commit()
        await db.refresh(obj)
        return obj
    return await ip_create(db, data)

async def ip_get(db: AsyncSession, cod: int) -> Optional[ClientIPs]:
    return await db.get(ClientIPs, cod)

async def ip_list_by_client(db: AsyncSession, integration_client_cod: int) -> Sequence[ClientIPs]:
    stmt = select(ClientIPs).where(ClientIPs.integrationClientCod == integration_client_cod).order_by(ClientIPs.codClientIp.desc())
    res = await db.execute(stmt)
    return res.scalars().all()

async def ip_update(db: AsyncSession, cod: int, data: ClientIpUpdate) -> Optional[ClientIPs]:
    obj = await ip_get(db, cod)
    if not obj:
        return None
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    await db.commit()
    await db.refresh(obj)
    return obj

async def ip_delete(db: AsyncSession, cod: int) -> bool:
    obj = await ip_get(db, cod)
    if not obj:
        return False
    await db.delete(obj)
    await db.commit()
    return True
