# app/core/database/bootstrap_app_scheme/idempotency_keys.py
from __future__ import annotations
from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Integer, String, Boolean, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import TIMESTAMP, JSONB
from sqlalchemy.sql import func

from . import schema_name


class IdempotencyKeys(SQLModel, table=True):
    __tablename__ = "idempotency_keys"
    __table_args__ = (UniqueConstraint("client_id", "key", name="uq_client_idem"),{"schema": schema_name})
    codIdempotencyKeys: Optional[int] = Field(default=None,sa_column=Column("cod_idempotency_keys", Integer, primary_key=True, autoincrement=True))
    createDate: datetime = Field(sa_column=Column("create_date", TIMESTAMP(timezone=True), nullable=False, server_default=func.now()))
    updateDate: Optional[datetime] = Field(default=None,sa_column=Column("update_date", TIMESTAMP(timezone=True), onupdate=func.now()))
    deleteDate: Optional[datetime] = Field(default=None,sa_column=Column("delete_date", TIMESTAMP(timezone=True)))
    createUser: int = Field(sa_column=Column("create_user", Integer, nullable=False))
    userAt: int = Field(sa_column=Column("user_at", Integer, nullable=False))
    active: bool = Field(default=True, sa_column=Column("active", Boolean, nullable=False, server_default=text("true")))
    clientId: str = Field(sa_column=Column("client_id", String(64), nullable=False, index=True))
    key: str = Field(sa_column=Column("key", String(128), nullable=False))
    requestFingerprint: str = Field(sa_column=Column("request_fingerprint", String(64), nullable=False))
    responseJson: Optional[dict] = Field(default=None, sa_column=Column("response_json", JSONB))
    httpStatus: Optional[int] = Field(default=None, sa_column=Column("http_status", Integer))
    status: str = Field(default="processing",sa_column=Column("status", String(16), nullable=False, server_default="processing"))
