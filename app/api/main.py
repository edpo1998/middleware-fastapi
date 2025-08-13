from fastapi import APIRouter

from app.api.routes import items, login, private, users, utils
from app.api.routes.invoices import invoices_router
from app.core.config import settings

api_router = APIRouter()
api_router.include_router(login.router)
api_router.include_router(invoices_router, tags=["invoices"])
api_router.include_router(users.router)
api_router.include_router(utils.router)
api_router.include_router(items.router)


if settings.app.ENVIRONMENT == "local":
    api_router.include_router(private.router)