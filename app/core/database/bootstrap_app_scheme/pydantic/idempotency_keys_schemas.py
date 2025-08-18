from datetime import datetime
from typing import Optional, Any
from sqlmodel import SQLModel, Field

class IdempotencyKeyCreate(SQLModel):
    createUser: int
    userAt: int
    clientId: str = Field(min_length=1, max_length=64)
    key: str = Field(min_length=1, max_length=128)
    requestFingerprint: str = Field(min_length=1, max_length=64)
    active: bool = True
    # status se setea a "processing" del lado modelo/DB por default

class IdempotencyKeyUpdate(SQLModel):
    createUser: Optional[int] = None
    userAt: Optional[int] = None
    responseJson: Optional[dict] = None
    httpStatus: Optional[int] = None
    status: Optional[str] = None
    active: Optional[bool] = None
    deleteDate: Optional[datetime] = None

class IdempotencyKeyOut(SQLModel):
    codIdempotencyKeys: int
    createDate: datetime
    updateDate: Optional[datetime]
    deleteDate: Optional[datetime]
    createUser: int
    userAt: int
    active: bool
    clientId: str
    key: str
    requestFingerprint: str
    responseJson: Optional[dict]
    httpStatus: Optional[int]
    status: str

    model_config = {"from_attributes": True}
