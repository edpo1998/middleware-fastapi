"""
    Contiene logica para la informacion inicial para el modulo de seguridad de la aplicacion.
"""
from __future__ import annotations
import os
import asyncio
import logging
from typing import Optional

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select

from app.core.config import Settings
import app.core.database  # fuerza registro de metadata/modelos

from app.core.database.bootstrap_app_scheme.models import (
    IntegrationClients,
    ClientKeys,
    ClientIPs,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


CLIENT_ID = os.getenv("BOOTSTRAP_CLIENT_ID", "bootstrap-client")
CLIENT_NAME = os.getenv("BOOTSTRAP_CLIENT_NAME", "Bootstrap Client")
KEY_KID = os.getenv("BOOTSTRAP_KEY_KID", "bootstrap-kid")
KEY_SECRET = os.getenv("BOOTSTRAP_KEY_SECRET", "bootstrap-secret")
IP_CIDR = os.getenv("BOOTSTRAP_IP_CIDR", "127.0.0.1/32")


async def _get_or_create_client(session: AsyncSession) -> IntegrationClients:
    res = await session.execute(
        select(IntegrationClients).where(IntegrationClients.clientId == CLIENT_ID)
    )
    existing: Optional[IntegrationClients] = res.scalars().first()
    if existing:
        logger.info("Cliente ya existe: %s (cod=%s)", existing.clientId, existing.codIntegrationClient)
        return existing

    ic = IntegrationClients(
        createUser=1,
        userAt=1,
        active=True,
        clientId=CLIENT_ID,
        name=CLIENT_NAME,
    )
    session.add(ic)
    await session.flush()  # para tener codIntegrationClient
    logger.info("Cliente creado: %s (cod=%s)", ic.clientId, ic.codIntegrationClient)
    return ic


async def _ensure_key(session: AsyncSession, client: IntegrationClients) -> None:
    res = await session.execute(
        select(ClientKeys).where(
            (ClientKeys.integrationClientCod == client.codIntegrationClient)
            & (ClientKeys.kid == KEY_KID)
        )
    )
    exists = res.scalars().first()
    if exists:
        logger.info("Key ya existe (kid=%s)", KEY_KID)
        return
    ck = ClientKeys(
        createUser=1,
        userAt=1,
        active=True,
        integrationClientCod=client.codIntegrationClient,
        secret=KEY_SECRET,
        kid=KEY_KID,
        alg="HS256",
    )
    session.add(ck)
    logger.info("Key creada (kid=%s)", KEY_KID)


async def _ensure_ip(session: AsyncSession, client: IntegrationClients) -> None:
    res = await session.execute(
        select(ClientIPs).where(
            (ClientIPs.integrationClientCod == client.codIntegrationClient)
            & (ClientIPs.cidr == IP_CIDR)
        )
    )
    exists = res.scalars().first()
    if exists:
        logger.info("IP ya existe (cidr=%s)", IP_CIDR)
        return
    ip = ClientIPs(
        createUser=1,
        userAt=1,
        active=True,
        integrationClientCod=client.codIntegrationClient,
        cidr=IP_CIDR,
    )
    session.add(ip)
    logger.info("IP creada (cidr=%s)", IP_CIDR)


async def _run() -> None:
    settings = Settings()
    async_url = settings.db.SQLALCHEMY_DATABASE_URI
    engine = create_async_engine(async_url, pool_pre_ping=True, future=True)
    Session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    try:
        async with Session() as session:
            client = await _get_or_create_client(session)
            await _ensure_key(session, client)
            await _ensure_ip(session, client)
            await session.commit()
            logger.info("Datos de seguridad listos.")
    finally:
        await engine.dispose()


def main() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    main()
