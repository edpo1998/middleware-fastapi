from __future__ import annotations
from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.sql import func

from . import schema_name
from .integration_clients import IntegrationClients


class SecurityNonces(SQLModel, table=True):
    __tablename__ = "security_nonces"
    __table_args__ = (
        UniqueConstraint("client_id", "nonce", name="uq_nonce_per_client"),
        {"schema": schema_name},
    )

    codSecurityNonce: Optional[int] = Field( default=None,sa_column=Column("cod_security_nonce", Integer, primary_key=True, autoincrement=True))
    integrationClientCod: int = Field(sa_column=Column("integration_client_cod",ForeignKey(f"{schema_name}.integration_clients.cod_integration_client", ondelete="CASCADE"),nullable=False))
    createDate: datetime = Field(sa_column=Column("create_date", TIMESTAMP(timezone=True), nullable=False, server_default=func.now()))
    updateDate: Optional[datetime] = Field(default=None, sa_column=Column("update_date", TIMESTAMP(timezone=True), onupdate=func.now()))
    deleteDate: Optional[datetime] = Field(default=None, sa_column=Column("delete_date", TIMESTAMP(timezone=True)))
    createUser: int = Field(sa_column=Column("create_user", Integer, nullable=False))
    userAt: int = Field(sa_column=Column("user_at", Integer, nullable=False))
    active: bool = Field(default=True, sa_column=Column("active", Boolean, nullable=False, server_default=text("true")))

    clientId: str = Field(sa_column=Column("client_id", String(64), nullable=False, index=True))
    nonce: str = Field(sa_column=Column("nonce", String(64), nullable=False))  # base64url 16–64 chars
    requestTs: datetime = Field(sa_column=Column("request_ts", TIMESTAMP(timezone=True), nullable=False))
    receivedAt: datetime = Field(sa_column=Column("received_at", TIMESTAMP(timezone=True), nullable=False, server_default=func.now()))

    integrationClient: Optional[IntegrationClients] = Relationship(sa_relationship_kwargs={"lazy": "selectin"})
