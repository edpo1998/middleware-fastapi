from __future__ import annotations

import sys
from datetime import datetime, timedelta, UTC
import uuid

from sqlmodel import Session, select

# --- Ajusta estos imports según tu proyecto ---
from app.core.database.db import engine  # si no tienes engine aquí, importa get_session y crea Session
from app.core.security.security import get_password_hash

# Bootstrap / seguridad (HMAC)
from app.core.database.bootstrap_app__scheme import (
    IntegrationClients,
    ClientKeys,
    ClientIPs,
)

# Usuarios (JWT)
from app.core.database.mcs_scheme.users import User


# --------- Config de seed (puedes cambiar) ----------
CLIENT_ID = "logistaas-local"
CLIENT_NAME = "Logistaas Local"
KEY_ID = "K1"
KEY_SECRET = "devsecret123"
KEY_ALG = "HS256"
IP_ALLOWLIST = ["127.0.0.1/32", "::1/128"]

ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "changeme123"
ADMIN_FULLNAME = "Admin"
# ----------------------------------------------------


def upsert_integration_client(session: Session) -> IntegrationClients:
    now = datetime.now(UTC).replace(tzinfo=None)

    client = session.exec(
        select(IntegrationClients).where(
            IntegrationClients.clientId == CLIENT_ID
        )
    ).first()

    if client:
        # si existe, asegúrate que esté activo y con nombre correcto
        client.name = CLIENT_NAME
        client.active = True
        client.updateDate = now
        session.add(client)
        session.commit()
        session.refresh(client)
        print(f"[OK] IntegrationClient reutilizado: {client.clientId} (cod={client.codIntegrationClient})")
        return client

    client = IntegrationClients(
        createDate=now,
        updateDate=None,
        deleteDate=None,
        createUser=0,
        userAt=0,
        active=True,
        clientId=CLIENT_ID,
        name=CLIENT_NAME,
    )
    session.add(client)
    session.commit()
    session.refresh(client)
    print(f"[OK] IntegrationClient creado: {client.clientId} (cod={client.codIntegrationClient})")
    return client


def upsert_client_key(session: Session, client: IntegrationClients) -> ClientKeys:
    now = datetime.now(UTC).replace(tzinfo=None)
    key = session.exec(
        select(ClientKeys).where(
            ClientKeys.integrationClientCod == client.codIntegrationClient,
            ClientKeys.kid == KEY_ID
        )
    ).first()

    if key:
        key.secret = KEY_SECRET
        key.alg = KEY_ALG
        key.active = True
        key.updateDate = now
        session.add(key)
        session.commit()
        session.refresh(key)
        print(f"[OK] ClientKey reutilizada: kid={key.kid}")
        return key

    key = ClientKeys(
        createDate=now,
        updateDate=None,
        deleteDate=None,
        createUser=0,
        userAt=0,
        active=True,
        integrationClientCod=client.codIntegrationClient,
        expiresAt=now + timedelta(days=3650),  # ~10 años para dev
        lastUsedAt=now,
        secret=KEY_SECRET,
        alg=KEY_ALG,
        kid=KEY_ID,
    )
    session.add(key)
    session.commit()
    session.refresh(key)
    print(f"[OK] ClientKey creada: kid={key.kid}")
    return key


def ensure_client_ips(session: Session, client: IntegrationClients) -> None:
    existing = session.exec(
        select(ClientIPs).where(
            ClientIPs.integrationClientCod == client.codIntegrationClient
        )
    ).all()
    have = {row.cidr for row in existing}

    to_add = [cidr for cidr in IP_ALLOWLIST if cidr not in have]
    if not to_add:
        print("[OK] ClientIPs: allowlist ya presente")
        return

    now = datetime.now(UTC).replace(tzinfo=None)
    for cidr in to_add:
        session.add(ClientIPs(
            createDate=now,
            updateDate=None,
            deleteDate=None,
            createUser=0,
            userAt=0,
            active=True,
            integrationClientCod=client.codIntegrationClient,
            cidr=cidr,
        ))
    session.commit()
    print(f"[OK] ClientIPs añadidas: {', '.join(to_add)}")


def upsert_admin_user(session: Session) -> User:
    user = session.exec(
        select(User).where(User.email == ADMIN_EMAIL)
    ).first()

    if user:
        print(f"[OK] Admin reutilizado: {user.email}")
        return user

    hashed = get_password_hash(ADMIN_PASSWORD)
    user = User(
        id=uuid.uuid4(),
        email=ADMIN_EMAIL,
        full_name=ADMIN_FULLNAME,
        is_active=True,
        is_superuser=True,
        hashed_password=hashed,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    print(f"[OK] Admin creado: {user.email} (id={user.id})")
    return user


def main():
    print("== SEED LOCAL ==")
    with Session(engine) as session:
        client = upsert_integration_client(session)
        upsert_client_key(session, client)
        ensure_client_ips(session, client)
        upsert_admin_user(session)
    print("== DONE ==")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("[ERROR]", e)
        sys.exit(1)
