from typing import Optional
from sqlmodel import SQLModel, Field

class ClientIpCreate(SQLModel):
    integrationClientCod: int
    createUser: int
    userAt: int
    cidr: str = Field(min_length=1)
    active: bool = True

class ClientIpUpdate(SQLModel):
    createUser: Optional[int] = None
    userAt: Optional[int] = None
    cidr: Optional[str] = None
    active: Optional[bool] = None

class ClientIpOut(SQLModel):
    codClientIp: int
    integrationClientCod: int
    createUser: int
    userAt: int
    cidr: str
    active: bool

    model_config = {"from_attributes": True}
