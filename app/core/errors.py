import logging
from typing import Any, Dict, List
from fastapi import Request, status, HTTPException
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from app.core.config import settings

logger = logging.getLogger(__name__)



def _build_payload(
    request: Request,
    *,
    code: str,
    message: str,
    details: Any = None,
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
) -> JSONResponse:
    corr_id = request.headers.get("X-Request-ID") or getattr(request.state, "request_id", None)
    body: Dict[str, Any] = {
        "code": code,
        "message": message,
        "details": details,
        "correlation_id": corr_id,
        "path": request.url.path,
    }
    return JSONResponse(status_code=status_code, content=jsonable_encoder(body))



async def fastapi_http_exception_handler(request: Request, exc: HTTPException):
    detail = exc.detail if isinstance(exc.detail, str) else jsonable_encoder(exc.detail)
    return _build_payload(
        request,
        code=f"HTTP_{exc.status_code}",
        message=str(detail),
        status_code=exc.status_code,
    )



async def starlette_http_exception_handler(request: Request, exc: StarletteHTTPException):
    detail = exc.detail if isinstance(exc.detail, str) else jsonable_encoder(exc.detail)
    return _build_payload(
        request,
        code=f"HTTP_{exc.status_code}",
        message=str(detail),
        status_code=exc.status_code,
    )



async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors: List[Dict[str, Any]] = [
        {"loc": e.get("loc"), "msg": e.get("msg"), "type": e.get("type")}
        for e in exc.errors()
    ]
    return _build_payload(
        request,
        code="VALIDATION_ERROR",
        message="Validation failed",
        details={"errors": errors},
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
    )



async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    if isinstance(exc, IntegrityError):
        return _build_payload(
            request,
            code="DB_INTEGRITY_ERROR",
            message="Database integrity violation",
            status_code=status.HTTP_409_CONFLICT,
        )
    return _build_payload(
        request,
        code="DB_ERROR",
        message="Database error",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )



async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception", exc_info=exc, extra={"path": str(request.url)})
    if settings.app.DEBUG:
        return _build_payload(request, code="INTERNAL_ERROR", message="Internal server error", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    safe_details = {"type": exc.__class__.__name__, "message": str(exc)}
    return _build_payload(request, code="INTERNAL_ERROR", message="Internal server error", details=safe_details, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)