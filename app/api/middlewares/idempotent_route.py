from __future__ import annotations

import json
import hashlib
from typing import Optional

from fastapi.routing import APIRoute
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse

from app.core.database.db_async import AsyncSessionLocal
from app.core.security.idempotency import begin_idempotency, finalize_idempotency


_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


def _buffer_request_body(request: Request) -> None:
    """
    Lee el body y lo reinyecta para que el endpoint pueda volver a leerlo.
    """
    async def _injector(body: bytes):
        async def _receive():
            return {"type": "http.request", "body": body, "more_body": False}
        return _receive

    # Nota: llamante debe hacer await request.body() y luego asignar _receive
    # acá solo configuramos util por claridad.
    return None


def _fingerprint(method: str, path: str, query: str, body: bytes) -> str:
    h = hashlib.sha256()
    h.update(method.encode())
    h.update(b"|")
    h.update(path.encode())
    h.update(b"|")
    h.update((query or "").encode())
    h.update(b"|")
    h.update(body or b"")
    return h.hexdigest()


class IdempotentRoute(APIRoute):
    """
    APIRoute que añade idempotencia por Header:
      - Requiere:  Idempotency-Key y X-Client-Id.
      - Aplica solo a métodos de escritura (POST/PUT/PATCH/DELETE).
      - Cachea respuestas JSON; las no-JSON se marcan como success pero sin cuerpo guardado.

    Usa las helpers async: begin_idempotency / finalize_idempotency.
    """

    def get_route_handler(self):
        original_handler = super().get_route_handler()

        async def custom_handler(request: Request) -> Response:
            # Solo escritura y si viene el header
            if request.method.upper() not in _METHODS:
                return await original_handler(request)

            idem_key = request.headers.get("Idempotency-Key")
            client_id = request.headers.get("X-Client-Id")
            if not idem_key or not client_id:
                return await original_handler(request)

            # Buffer del body y reinyectar
            body = await request.body()
            async def _receive():
                return {"type": "http.request", "body": body, "more_body": False}
            request._receive = _receive

            # Huella del request (estable)
            fp = _fingerprint(request.method.upper(), request.url.path, request.url.query or "", body)

            # Intento de "begin" idempotente
            record_id: Optional[int] = None
            async with AsyncSessionLocal() as session:  # type: ignore
                idem = await begin_idempotency(
                    session,
                    client_id=client_id,
                    key=idem_key,
                    request_fingerprint=fp,
                )
                if idem.get("cached"):
                    data = idem.get("cached_body") or {}
                    status_code = int(idem.get("cached_status") or 200)
                    return JSONResponse(content=data, status_code=status_code)

                if idem.get("in_progress"):
                    raise HTTPException(status_code=409, detail="request in progress")

                record_id = idem.get("record_id")

            # Ejecuta el endpoint (incluye dependencias como HMAC)
            try:
                response: Response = await original_handler(request)

                # Capturar el body de la respuesta para guardarlo (si es JSON)
                content_bytes = b""
                # Para la mayoría de Responses (JSONResponse, Response):
                if hasattr(response, "body") and isinstance(response.body, (bytes, bytearray)):
                    content_bytes = bytes(response.body)
                else:
                    # StreamingResponse u otros: consumir iterator y reconstruir
                    if hasattr(response, "body_iterator") and response.body_iterator is not None:
                        async for chunk in response.body_iterator:
                            content_bytes += chunk

                # Reconstruir la respuesta (si consumimos el iterator)
                new_resp = Response(
                    content=content_bytes,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type=response.media_type,
                )

                # Intentar serializar JSON para almacenar
                payload = None
                if new_resp.media_type and "json" in new_resp.media_type.lower():
                    try:
                        payload = json.loads((content_bytes or b"").decode() or "null")
                    except Exception:
                        payload = None

                async with AsyncSessionLocal() as session:  # type: ignore
                    await finalize_idempotency(
                        session,
                        record_id=record_id,
                        http_status=new_resp.status_code,
                        response_obj=payload,
                    )

                return new_resp

            except HTTPException as he:
                async with AsyncSessionLocal() as session:  # type: ignore
                    await finalize_idempotency(
                        session,
                        record_id=record_id,
                        http_status=he.status_code,
                        response_obj={"detail": he.detail},
                    )
                raise
            except Exception:
                async with AsyncSessionLocal() as session:  # type: ignore
                    await finalize_idempotency(
                        session,
                        record_id=record_id,
                        http_status=500,
                        response_obj={"detail": "internal error"},
                    )
                raise

        return custom_handler
