from __future__ import annotations

import uuid
from typing import Sequence, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database.mcs_scheme.models.items import Item
from core.database.mcs_scheme.pydantic.items_schemas import ItemCreate, ItemUpdate


# ---------- CREATE ----------
async def create_item(
    db: AsyncSession,
    *,
    owner_id: uuid.UUID,
    data: ItemCreate,
) -> Item:
    obj = Item(
        owner_id=owner_id,
        title=data.title,
        description=data.description,
    )
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


# ---------- READ ----------
async def get_item(db: AsyncSession, item_id: uuid.UUID) -> Optional[Item]:
    return await db.get(Item, item_id)


async def list_items(
    db: AsyncSession,
    *,
    owner_id: uuid.UUID | None = None,
    q: str | None = None,
    offset: int = 0,
    limit: int = 50,
    order_desc: bool = True,
) -> Sequence[Item]:
    stmt = select(Item)
    if owner_id:
        stmt = stmt.where(Item.owner_id == owner_id)
    if q:
        like = f"%{q.lower()}%"
        stmt = stmt.where(func.lower(Item.title).like(like))
    stmt = stmt.order_by(Item.id.desc() if order_desc else Item.id.asc())
    stmt = stmt.offset(offset).limit(limit)
    res = await db.execute(stmt)
    return res.scalars().all()


async def count_items(
    db: AsyncSession, *, owner_id: uuid.UUID | None = None, q: str | None = None
) -> int:
    stmt = select(func.count(Item.id))
    if owner_id:
        stmt = stmt.where(Item.owner_id == owner_id)
    if q:
        like = f"%{q.lower()}%"
        stmt = stmt.where(func.lower(Item.title).like(like))
    res = await db.execute(stmt)
    return int(res.scalar_one())


# ---------- UPDATE ----------
async def update_item(
    db: AsyncSession,
    item_id: uuid.UUID,
    data: ItemUpdate,
) -> Optional[Item]:
    obj = await get_item(db, item_id)
    if not obj:
        return None

    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)

    await db.commit()
    await db.refresh(obj)
    return obj


# ---------- DELETE ----------
async def delete_item(db: AsyncSession, item_id: uuid.UUID) -> bool:
    obj = await get_item(db, item_id)
    if not obj:
        return False
    await db.delete(obj)
    await db.commit()
    return True
