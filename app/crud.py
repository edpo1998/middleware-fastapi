from __future__ import annotations
import uuid
from typing import Any, Sequence

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

from app.core.security.security import get_password_hash, verify_password
from app.core.database.mcs_scheme.models import User, Item
from app.core.database.mcs_scheme.pydantic import (
    UserCreate, UserUpdate, ItemCreate
)


# ---------------- USERS ----------------

async def get_user(*, session: AsyncSession, user_id: uuid.UUID) -> User | None:
    res = await session.execute(select(User).where(User.id == user_id))
    return res.scalar_one_or_none()

async def get_user_by_email(*, session: AsyncSession, email: str) -> User | None:
    res = await session.execute(select(User).where(User.email == email))
    return res.scalar_one_or_none()

async def list_users(*, session: AsyncSession, skip: int = 0, limit: int = 100) -> Sequence[User]:
    res = await session.execute(select(User).offset(skip).limit(limit))
    return list(res.scalars().all())

async def create_user(*, session: AsyncSession, user_in: UserCreate) -> User:
    hashed = get_password_hash(user_in.password)
    db_user = User.model_validate(user_in, update={"hashed_password": hashed})
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)
    return db_user

async def upsert_user_by_email(*, session, user_in, is_superuser: bool | None = None) -> User:
    values = {
        "email": user_in.email,
        "hashed_password": get_password_hash(user_in.password),
        "full_name": user_in.full_name,
    }
    if is_superuser is not None:
        values["is_superuser"] = is_superuser

    # 👇 clave: si el insert ocurre (no hay conflicto), mandamos un UUID para id
    values.setdefault("id", uuid.uuid4())

    stmt = (
        insert(User)
        .values(**values)
        .on_conflict_do_update(
            index_elements=[User.__table__.c.email],
            set_={k: v for k, v in values.items() if k not in ("email", "id")},
        )
        .returning(User)
    )
    res = await session.execute(stmt)
    await session.commit()
    return res.scalar_one()

async def update_user(*, session: AsyncSession, db_user: User, user_in: UserUpdate) -> User:
    data: dict[str, Any] = user_in.model_dump(exclude_unset=True)
    if "password" in data and data["password"]:
        data["hashed_password"] = get_password_hash(data.pop("password"))
    for k, v in data.items():
        setattr(db_user, k, v)
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)
    return db_user

async def authenticate(*, session: AsyncSession, email: str, password: str) -> User | None:
    user = await get_user_by_email(session=session, email=email)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


# ---------------- ITEMS ----------------

async def create_item(*, session: AsyncSession, owner_id: uuid.UUID, item_in: ItemCreate) -> Item:
    db_item = Item.model_validate(item_in, update={"owner_id": owner_id})
    session.add(db_item)
    await session.commit()
    await session.refresh(db_item)
    return db_item

async def list_items_by_owner(
    *, session: AsyncSession, owner_id: uuid.UUID, skip: int = 0, limit: int = 100
) -> Sequence[Item]:
    res = await session.execute(
        select(Item).where(Item.owner_id == owner_id).offset(skip).limit(limit)
    )
    return list(res.scalars().all())

async def delete_item(*, session: AsyncSession, item_id: uuid.UUID) -> None:
    await session.execute(delete(Item).where(Item.id == item_id))
    await session.commit()
