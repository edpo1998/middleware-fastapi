from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field

class ClientKeyCreate(SQLModel):
    integrationClientCod: int
    createUser: int
    userAt: int
    secret: str = Field(min_length=1)
    kid: str = Field(min_length=1, max_length=64)
    alg: str = "HS256"
    expiresAt: Optional[datetime] = None
    active: bool = True

class ClientKeyUpdate(SQLModel):
    createUser: Optional[int] = None
    userAt: Optional[int] = None
    secret: Optional[str] = None
    kid: Optional[str] = Field(default=None, min_length=1, max_length=64)
    alg: Optional[str] = None
    expiresAt: Optional[datetime] = None
    lastUsedAt: Optional[datetime] = None
    active: Optional[bool] = None

class ClientKeyOut(SQLModel):
    codClientKey: int
    createDate: datetime
    updateDate: Optional[datetime]
    deleteDate: Optional[datetime]
    createUser: int
    userAt: int
    active: bool
    integrationClientCod: int
    expiresAt: Optional[datetime]
    lastUsedAt: Optional[datetime]
    secret: str
    alg: str
    kid: str

    model_config = {"from_attributes": True}
