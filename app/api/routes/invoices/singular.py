from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy import select

from app.api.middlewares import IdempotentRoute          
from app.core.security.hmac_auth import hmac_auth    
from app.api.deps import SessionDep                 
from app.core.database.mcs_scheme.models import User 

router = APIRouter(route_class=IdempotentRoute)

@router.post("/invoices", dependencies=[Depends(hmac_auth)])
async def create_invoice(
    request: Request,
    session: SessionDep,
):
    result = await session.execute(select(User).order_by(User.id).limit(1))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(status_code=404, detail="No users found")

    return JSONResponse(
        status_code=201,
        content={
            "user": {
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "is_active": bool(user.is_active),
                "is_superuser": bool(user.is_superuser),
            },
            "message": "invoice created (dummy payload)",
        },
    )
