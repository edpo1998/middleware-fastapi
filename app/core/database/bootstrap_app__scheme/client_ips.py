# app/core/database/bootstrap_app_scheme/client_ips.py
from __future__ import annotations
from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import TIMESTAMP, CIDR
from sqlalchemy.sql import func

from . import schema_name
from .integration_clients import IntegrationClients


class ClientIPs(SQLModel, table=True):
    __tablename__ = "client_ips"
    __table_args__ = (UniqueConstraint("integration_client_cod", "cidr", name="uq_client_ip_per_client"),{"schema": schema_name})
    codClientIp: Optional[int] = Field(default=None,sa_column=Column("cod_client_ip", Integer, primary_key=True, autoincrement=True))
    createDate: datetime = Field(sa_column=Column("create_date", TIMESTAMP(timezone=True), nullable=False, server_default=func.now()))
    updateDate: Optional[datetime] = Field(default=None,sa_column=Column("update_date", TIMESTAMP(timezone=True), onupdate=func.now()))
    deleteDate: Optional[datetime] = Field(default=None,sa_column=Column("delete_date", TIMESTAMP(timezone=True)))
    createUser: int = Field(sa_column=Column("create_user", Integer, nullable=False))
    userAt: int = Field(sa_column=Column("user_at", Integer, nullable=False))
    active: bool = Field(default=True,sa_column=Column("active", Boolean, nullable=False, server_default=text("true")))
    integrationClientCod: int = Field(sa_column=Column("integration_client_cod",ForeignKey(f"{schema_name}.integration_clients.cod_integration_client", ondelete="CASCADE"),nullable=False))
    cidr: str = Field(sa_column=Column("cidr", CIDR, nullable=False))
    
    integrationClient: Optional[IntegrationClients] = Relationship(back_populates="ips",sa_relationship_kwargs={"lazy": "selectin"},)
