import uuid
from typing import Optional, List

from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import text, String, Boolean
from sqlalchemy.dialects.postgresql import UUID
from . import schema_name

class User(SQLModel, table=True):
    __tablename__ = "users"
    __table_args__ = {"schema": schema_name}

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(UUID(as_uuid=True), primary_key=True)
    )
    email: str = Field(
        sa_column=Column("email", String(255), unique=True, index=True, nullable=False),
    )
    hashed_password: str = Field(sa_column=Column("hashed_password", String(255), nullable=False))
    is_active: bool = Field(default=True, sa_column=Column("is_active", Boolean, nullable=False, server_default=text("true")))
    is_superuser: bool = Field(default=False, sa_column=Column("is_superuser", Boolean, nullable=False, server_default=text("false")))
    full_name: Optional[str] = Field(sa_column=Column("full_name", String(255)))


    items: List["Item"] = Relationship(
        back_populates="owner",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
