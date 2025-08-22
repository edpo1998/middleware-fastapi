# app/models/invoice.py
from __future__ import annotations
from enum import Enum
from typing import Optional, Any
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Column, JSON, Integer, Boolean
from . import schema_name
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.sql import func

class MonitorStatus(str, Enum):
    draft = "draft"
    posting = "posting"
    posted = "posted"
    failed = "failed"

class Monitor(SQLModel, table=True):
    __tablename__ = "monitor"
    __table_args__ = {"schema": schema_name}

    id: Optional[int] = Field(default=None, primary_key=True)
    document: str = Field(sa_column=Column("document", Integer, nullable=False))
    status: MonitorStatus = Field(default=None, index=True)
    payload_client: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    payload_sap: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    error_details: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    sap_doc_entry: Optional[int] = Field(default=None, index=True)
    sap_doc_num: Optional[int] = Field(default=None, index=True)
    version: int = Field(default=1, description="Optimistic locking")
    created_at: datetime = Field(sa_column=Column("created_at", TIMESTAMP(timezone=True), nullable=False, server_default=func.now()))
    updated_at: datetime = Field(sa_column=Column("updated_at", TIMESTAMP(timezone=True), nullable=False, server_default=func.now()))