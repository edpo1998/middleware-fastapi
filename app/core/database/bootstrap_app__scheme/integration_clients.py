# app/core/database/bootstrap_app_scheme/integration_clients.py
from __future__ import annotations
from datetime import datetime
from typing import List, Optional, TYPE_CHECKING

from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, Integer, String, Boolean, text
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.sql import func
from . import schema_name

if TYPE_CHECKING:
    from .client_keys import ClientKeys
    from .client_ips import ClientIPs

class IntegrationClients(SQLModel, table=True):
    __tablename__ = "integration_clients"
    __table_args__ = {"schema": schema_name}

    codIntegrationClient: Optional[int] = Field(default=None, sa_column=Column("cod_integration_client", Integer, primary_key=True, autoincrement=True))
    createDate: datetime = Field( sa_column=Column("create_date", TIMESTAMP(timezone=True), nullable=False, server_default=func.now()))
    updateDate: Optional[datetime] = Field(default=None,sa_column=Column("update_date", TIMESTAMP(timezone=True), onupdate=func.now()))
    deleteDate: Optional[datetime] = Field(default=None,sa_column=Column("delete_date", TIMESTAMP(timezone=True)))
    createUser: int = Field(sa_column=Column("create_user", Integer, nullable=False))
    userAt: int = Field(sa_column=Column("user_at", Integer, nullable=False))
    active: bool = Field(default=True, sa_column=Column("active", Boolean, nullable=False, server_default=text("true")))
    clientId: str = Field(sa_column=Column("client_id", String(64), unique=True, index=True, nullable=False))
    name: str = Field(sa_column=Column("name", String(255), nullable=False))

    keys: List["ClientKeys"] = Relationship(back_populates="integrationClient",sa_relationship_kwargs={"lazy": "selectin", "cascade": "all, delete-orphan"})
    ips: List["ClientIPs"] = Relationship(back_populates="integrationClient",sa_relationship_kwargs={"lazy": "selectin", "cascade": "all, delete-orphan"})
