from __future__ import annotations
import os
import asyncio
import logging

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.core.config import Settings
from app.core.database import metadata
from app.crud import (
    upsert_user_by_email, list_items_by_owner, create_item
)
from app.core.database.mcs_scheme.pydantic import UserCreate, ItemCreate

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def _get_superuser_from_env(settings: Settings) -> tuple[str, str, str]:
    email = None
    pwd = None
    name = None
    sec = getattr(settings, "security", None)
    if sec is not None:
        email = getattr(sec, "first_superuser", None)
        pwd = getattr(sec, "first_superuser_password", None)
        name = getattr(sec, "first_superuser_name", None)
    email = email or os.getenv("SECURITY__FIRST_SUPERUSER")
    pwd = pwd or os.getenv("SECURITY__FIRST_SUPERUSER_PASSWORD")
    name = name or os.getenv("SECURITY__FIRST_SUPERUSER_NAME") or "Admin"
    email = (email or "admin@example.com").strip()
    pwd = (pwd or "ChangeMe123!").strip()
    name = name.strip()
    return email, pwd, name


async def _run():
    settings = Settings()
    engine = create_async_engine(
        settings.db.SQLALCHEMY_DATABASE_URI,
        echo=False,
        pool_pre_ping=True,
        future=True,
    )
    SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)
    first_su_email, first_su_pwd, first_su_name = _get_superuser_from_env(settings)
    async with SessionLocal() as session:
        admin = await upsert_user_by_email(
            session=session,
            user_in=UserCreate(
                email=first_su_email,
                password=first_su_pwd,
                full_name=first_su_name,
            ),
            is_superuser=True,
        )
        log.info("Superusuario listo: %s", admin.email)
        items = await list_items_by_owner(session=session, owner_id=admin.id, limit=1)
        if not items:
            await create_item(
                session=session,
                owner_id=admin.id,
                item_in=ItemCreate(
                    title="Welcome",
                    description="Primer item del superusuario",
                ),
            )
            log.info("Item demo creado para superusuario")
    await engine.dispose()


def main():
    asyncio.run(_run())

if __name__ == "__main__":
    main()
