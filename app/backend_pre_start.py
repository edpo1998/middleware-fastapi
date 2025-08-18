# app/backend_pre_start.py
from __future__ import annotations
import asyncio
import logging
import socket
from contextlib import closing

from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import create_async_engine
from tenacity import retry, stop_after_attempt, wait_fixed, before_sleep_log

from app.core.config import Settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

RETRIES = 30
WAIT_SEC = 2

settings = Settings()
ASYNC_URL: URL = settings.db.SQLALCHEMY_DATABASE_URI  # objeto URL (postgresql+asyncpg)

def _tcp_check(host: str, port: int, timeout: float = 2.0) -> bool:
    try:
        with closing(socket.create_connection((host, port), timeout=timeout)):
            return True
    except OSError:
        return False

@retry(
    stop=stop_after_attempt(RETRIES),
    wait=wait_fixed(WAIT_SEC),
    reraise=True,
    before_sleep=before_sleep_log(logger, logging.WARNING),
)
async def _ping_db_once() -> None:
    logger.info(
        "Intentando conectar a DB: host=%s port=%s db=%s user=%s (timeout=%ss)",
        ASYNC_URL.host, ASYNC_URL.port, ASYNC_URL.database, ASYNC_URL.username, 3
    )

    if ASYNC_URL.host and ASYNC_URL.port and not _tcp_check(ASYNC_URL.host, int(ASYNC_URL.port)):
        raise ConnectionError(f"No hay TCP a {ASYNC_URL.host}:{ASYNC_URL.port} (¿container caído? ¿puerto mapeado?)")

    engine = create_async_engine(
        ASYNC_URL,
        pool_pre_ping=True,
        future=True,
        echo=False,
        connect_args={"timeout": 3.0},  # <- ¡timeout como float, aquí va bien!
    )

    try:
        async with engine.connect() as conn:
            # ✅ Llamada async -> await; consumo del Result -> síncrono
            res = await conn.exec_driver_sql("SELECT 1")
            _ = res.scalar()  # o res.fetchone()

            res = await conn.exec_driver_sql(
                "select current_database(), current_user, "
                "inet_server_addr(), inet_server_port(), current_setting('search_path')"
            )
            db, user, host, port, search_path = res.fetchone()  # <- sin await
            logger.info(
                "DB OK -> database=%s user=%s host=%s port=%s search_path=%s",
                db, user, host, port, search_path
            )
    except Exception as e:
        logger.exception("DB aún no lista / fallo de conexión: %s", e)
        raise
    finally:
        await engine.dispose()

def main() -> None:
    logger.info("Inicializando chequeo de base de datos (async)")
    try:
        asyncio.run(_ping_db_once())
    except Exception as e:
        logger.error("❌ No se pudo conectar a la base tras %s intentos: %s", RETRIES, e)
        raise SystemExit(1)
    logger.info("✅ Conexión verificada")

if __name__ == "__main__":
    main()
