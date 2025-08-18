from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field

class IntegrationClientCreate(SQLModel):
    createUser: int
    userAt: int
    clientId: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=255)
    active: bool = True

class IntegrationClientUpdate(SQLModel):
    createUser: Optional[int] = None
    userAt: Optional[int] = None
    clientId: Optional[str] = Field(default=None, min_length=1, max_length=64)
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    active: Optional[bool] = None
    deleteDate: Optional[datetime] = None  # por si manejas soft-delete

class IntegrationClientOut(SQLModel):
    codIntegrationClient: int
    createDate: datetime
    updateDate: Optional[datetime]
    deleteDate: Optional[datetime]
    createUser: int
    userAt: int
    active: bool
    clientId: str
    name: str

    model_config = {"from_attributes": True}
