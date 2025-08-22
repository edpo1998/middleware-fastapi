from datetime import datetime
from typing import TYPE_CHECKING, ClassVar

from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Integer, String, Boolean, text
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from . import schema_name

if TYPE_CHECKING:
    from .client_keys import ClientKeys
    from .client_ips import ClientIPs

class IntegrationClients(SQLModel, table=True):
    __tablename__ = "integration_clients"
    __table_args__ = {"schema": schema_name}

    codIntegrationClient: int | None = Field(
        default=None,
        sa_column=Column("cod_integration_client", Integer, primary_key=True, autoincrement=True),
    )
    createDate: datetime = Field(sa_column=Column("create_date", TIMESTAMP(timezone=True), nullable=False, server_default=func.now()))
    updateDate: datetime | None = Field(default=None, sa_column=Column("update_date", TIMESTAMP(timezone=True), onupdate=func.now()))
    deleteDate: datetime | None = Field(default=None, sa_column=Column("delete_date", TIMESTAMP(timezone=True)))
    createUser: int = Field(sa_column=Column("create_user", Integer, nullable=False))
    userAt: int = Field(sa_column=Column("user_at", Integer, nullable=False))
    active: bool = Field(default=True, sa_column=Column("active", Boolean, nullable=False, server_default=text("true")))
    clientId: str = Field(sa_column=Column("client_id", String(64), unique=True, nullable=False))
    name: str = Field(sa_column=Column("name", String(255), nullable=False))

    # 👇 Pydantic ignora (ClassVar); SQLAlchemy sí mapea
    keys: ClassVar[list["ClientKeys"]] = relationship(
        "ClientKeys",
        back_populates="integrationClient",
        lazy="selectin",
        cascade="all, delete-orphan",
        uselist=True
    )
    ips: ClassVar[list["ClientIPs"]] = relationship(
        "ClientIPs",
        back_populates="integrationClient",
        lazy="selectin",
        cascade="all, delete-orphan",
        uselist=True
    )
