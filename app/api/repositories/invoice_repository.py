# app/repositories/invoice_repo.py
from __future__ import annotations
from typing import Optional
from sqlmodel import Session
from app.core.database.mcs_scheme.models.monitor import Monitor

class InvoiceRepository:
    def __init__(self, session: Session):
        self.session = session

    async def get(self, id_: int) -> Monitor | None:
        return await self.session.get(Monitor, id_)