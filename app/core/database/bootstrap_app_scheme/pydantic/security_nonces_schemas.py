from datetime import datetime
from sqlmodel import SQLModel, Field

class SecurityNonceCreate(SQLModel):
    integrationClientCod: int
    createUser: int
    userAt: int
    clientId: str = Field(min_length=1, max_length=64)
    nonce: str = Field(min_length=16, max_length=64)  # base64url
    requestTs: datetime

class SecurityNonceOut(SQLModel):
    codSecurityNonce: int
    integrationClientCod: int
    createDate: datetime
    updateDate: datetime | None
    deleteDate: datetime | None
    createUser: int
    userAt: int
    active: bool
    clientId: str
    nonce: str
    requestTs: datetime
    receivedAt: datetime

    model_config = {"from_attributes": True}
