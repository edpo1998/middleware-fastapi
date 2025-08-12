from __future__ import annotations
import uuid
from typing import TYPE_CHECKING, Optional, List

from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlmodel import SQLModel, Field, Relationship

from . import schema_name

if TYPE_CHECKING:
    from .users import User

class ItemBase(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)


class ItemCreate(ItemBase):
    pass


class ItemUpdate(ItemBase):
    title: str | None = Field(default=None, min_length=1, max_length=255)  # type: ignore


class Item(ItemBase, table=True):
    __tablename__ = "items"
    __table_args__ = {"schema": schema_name}

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column("id", PGUUID(as_uuid=True), primary_key=True),
    )

    title: str = Field(
        sa_column=Column("title", String(255), nullable=False)
    )
    description: str | None = Field(
        default=None,
        sa_column=Column("description", String(255), nullable=True)
    )

    owner_id: uuid.UUID = Field(
        sa_column=Column(
            "owner_id",
            PGUUID(as_uuid=True),
            ForeignKey(f'{schema_name}.users.id', ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )

    owner: Optional["User"] = Relationship(
        back_populates="items",
        sa_relationship_kwargs={"lazy": "selectin"},
    )


class ItemPublic(ItemBase):
    id: uuid.UUID
    owner_id: uuid.UUID


class ItemsPublic(SQLModel):
    data: List[ItemPublic]
    count: int


class Message(SQLModel):
    message: str


class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(SQLModel):
    sub: str | None = None


class NewPassword(SQLModel):
    token: str
    new_password: str = Field(min_length=8, max_length=40)
