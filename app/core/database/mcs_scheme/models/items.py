import uuid
from typing import Optional

from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import ForeignKey, String
from . import schema_name

class Item(SQLModel, table=True):
    __tablename__ = "items"
    __table_args__ = {"schema": schema_name}

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(UUID(as_uuid=True), primary_key=True)
    )
    title: str = Field(
        sa_column=Column("title", String(255)),
    )
    description: Optional[str]  = Field(
        sa_column=Column("description", String(255)),
    )
    owner_id: uuid.UUID = Field(
        sa_column=Column(
            UUID(as_uuid=True),
            ForeignKey(f"{schema_name}.users.id", ondelete="CASCADE"),
            nullable=False,
        )
    )
    owner: Optional["User"] = Relationship(back_populates="items")
