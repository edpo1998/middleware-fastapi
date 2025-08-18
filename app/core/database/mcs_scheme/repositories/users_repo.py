from __future__ import annotations

import uuid
from typing import Sequence, Tuple, Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database.mcs_scheme.models.users import User
from core.database.mcs_scheme.pydantic.users_schemas import UserCreate, UserUpdate

# Si ya tienes utilidades de seguridad, importa aquí:
# from app.security.utils import get_password_hash, verify_password
def get_password_hash(raw: str) -> str:
    # ⚠️ Reemplaza por tu implementación real (bcrypt/argon2)
    # Dejo placeholder para que el repo no dependa de una lib aquí.
    import hashlib
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


# ---------- CREATE ----------
async def create_user(db: AsyncSession, data: UserCreate) -> User:
    """
    Crea un usuario. Lanza IntegrityError si email ya existe.
    """
    obj = User(
        email=str(data.email).lower(),
        hashed_password=get_password_hash(data.password),
        is_active=data.is_active,
        is_superuser=data.is_superuser,
        full_name=data.full_name,
    )
    db.add(obj)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise
    await db.refresh(obj)
    return obj


# ---------- READ ----------
async def get_user(db: AsyncSession, user_id: uuid.UUID) -> Optional[User]:
    return await db.get(User, user_id)


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    stmt = select(User).where(User.email == email.lower())
    res = await db.execute(stmt)
    return res.scalars().first()


async def list_users(
    db: AsyncSession,
    *,
    q: str | None = None,
    offset: int = 0,
    limit: int = 50,
    order_desc: bool = True,
) -> Sequence[User]:
    stmt = select(User)
    if q:
        like = f"%{q.lower()}%"
        stmt = stmt.where(
            func.lower(User.email).like(like) | func.lower(User.full_name).like(like)
        )
    stmt = stmt.order_by(User.id.desc() if order_desc else User.id.asc())
    stmt = stmt.offset(offset).limit(limit)
    res = await db.execute(stmt)
    return res.scalars().all()


async def count_users(db: AsyncSession, *, q: str | None = None) -> int:
    stmt = select(func.count(User.id))
    if q:
        like = f"%{q.lower()}%"
        stmt = stmt.where(
            func.lower(User.email).like(like) | func.lower(User.full_name).like(like)
        )
    res = await db.execute(stmt)
    return int(res.scalar_one())


# ---------- UPDATE ----------
async def update_user(
    db: AsyncSession,
    user_id: uuid.UUID,
    data: UserUpdate,
) -> Optional[User]:
    obj = await get_user(db, user_id)
    if not obj:
        return None

    payload = data.model_dump(exclude_unset=True)
    # email si viene, normalízalo
    if "email" in payload and payload["email"] is not None:
        payload["email"] = str(payload["email"]).lower()

    # password si viene, hashearlo y mapear a hashed_password
    if "password" in payload and payload["password"]:
        obj.hashed_password = get_password_hash(payload.pop("password"))

    for k, v in payload.items():
        setattr(obj, k, v)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise
    await db.refresh(obj)
    return obj


async def update_user_password(
    db: AsyncSession, user_id: uuid.UUID, new_password: str
) -> bool:
    obj = await get_user(db, user_id)
    if not obj:
        return False
    obj.hashed_password = get_password_hash(new_password)
    await db.commit()
    return True


# ---------- DELETE ----------
async def delete_user(db: AsyncSession, user_id: uuid.UUID) -> bool:
    obj = await get_user(db, user_id)
    if not obj:
        return False
    await db.delete(obj)
    await db.commit()
    return True
