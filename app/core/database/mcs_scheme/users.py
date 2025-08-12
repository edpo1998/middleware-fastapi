from __future__ import annotations
import uuid
from typing import TYPE_CHECKING, List

from pydantic import EmailStr
from sqlalchemy import Column, String, Boolean, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlmodel import SQLModel, Field, Relationship

from . import schema_name

if TYPE_CHECKING:
    from .items import Item  # solo para tipado (evita ciclos)


# -------- DTOs / modelos pydantic (no tabla) --------
class UserBase(SQLModel):
    email: EmailStr = Field(max_length=255)  # unicidad/índice se definen en la tabla
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=40)


class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=40)
    full_name: str | None = Field(default=None, max_length=255)


class UserUpdate(UserBase):
    email: EmailStr | None = Field(default=None, max_length=255)  # type: ignore
    password: str | None = Field(default=None, min_length=8, max_length=40)


class UserUpdateMe(SQLModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=40)
    new_password: str = Field(min_length=8, max_length=40)


# -------- Tabla --------
class User(UserBase, table=True):
    __tablename__ = "users"
    __table_args__ = {"schema": schema_name}

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column("id", PGUUID(as_uuid=True), primary_key=True),
    )

    # re-declaramos email con constraints de BD (unique + index + NOT NULL)
    email: EmailStr = Field(
        sa_column=Column("email", String(255), nullable=False, unique=True, index=True)
    )

    # re-declaramos full_name para evitar AutoString en migraciones
    full_name: str | None = Field(
        default=None,
        sa_column=Column("full_name", String(255), nullable=True),
    )

    # flags persistidos como columnas booleanas
    is_active: bool = Field(
        default=True,
        sa_column=Column("is_active", Boolean, nullable=False, server_default=text("true")),
    )
    is_superuser: bool = Field(
        default=False,
        sa_column=Column("is_superuser", Boolean, nullable=False, server_default=text("false")),
    )

    # hashed_password persistido en BD
    hashed_password: str = Field(
        sa_column=Column("hashed_password", String(255), nullable=False)
    )

    # relación con Item (sin ciclos; cascada en ORM)
    items: List["Item"] = Relationship(
        back_populates="owner",
        sa_relationship_kwargs={"lazy": "selectin", "cascade": "all, delete-orphan"},
    )


# -------- Respuestas --------
class UserPublic(UserBase):
    id: uuid.UUID


class UsersPublic(SQLModel):
    data: List[UserPublic]
    count: int
