# app/core/database/bootstrap_app_scheme/client_keys.py
from __future__ import annotations
from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.sql import func

from . import schema_name
from .integration_clients import IntegrationClients


class ClientKeys(SQLModel, table=True):
    __tablename__ = "client_keys"
    __table_args__ = (
        UniqueConstraint("integration_client_cod", "kid", name="uq_integration_client_kid"),
        {"schema": schema_name},
    )

    codClientKey: Optional[int] = Field(default=None, sa_column=Column("cod_client_key", Integer, primary_key=True, autoincrement=True))
    createDate: datetime = Field(sa_column=Column("create_date", TIMESTAMP(timezone=True), nullable=False, server_default=func.now()))
    updateDate: Optional[datetime] = Field(default=None, sa_column=Column("update_date", TIMESTAMP(timezone=True), onupdate=func.now()))
    deleteDate: Optional[datetime] = Field(default=None, sa_column=Column("delete_date", TIMESTAMP(timezone=True)))
    createUser: int = Field(sa_column=Column("create_user", Integer, nullable=False))
    userAt: int = Field(sa_column=Column("user_at", Integer, nullable=False))
    active: bool = Field( default=True, sa_column=Column("active", Boolean, nullable=False, server_default=text("true")))
    integrationClientCod: int = Field(sa_column=Column("integration_client_cod", ForeignKey(f"{schema_name}.integration_clients.cod_integration_client", ondelete="CASCADE"), nullable=False))
    expiresAt: Optional[datetime] = Field( default=None, sa_column=Column("expires_at", TIMESTAMP(timezone=True)))
    lastUsedAt: Optional[datetime] = Field( default=None, sa_column=Column("last_used_at", TIMESTAMP(timezone=True)))
    secret: str = Field(sa_column=Column("secret", String, nullable=False))  # TODO: Cifrado
    alg: str = Field(default="HS256", sa_column=Column("alg", String(16), nullable=False, server_default="HS256"))
    kid: str = Field(sa_column=Column("kid", String(64), nullable=False))

    integrationClient: "IntegrationClients" | None = Relationship(back_populates="keys")