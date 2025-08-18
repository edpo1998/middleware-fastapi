import sentry_sdk
from fastapi import FastAPI
from fastapi.routing import APIRoute
from starlette.middleware.cors import CORSMiddleware

import app.core.database 
from app.api.main import api_router
from app.core.config import settings


def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"


if settings.monitoring.SENTRY_DSN and settings.app.ENVIRONMENT != "local":
    sentry_sdk.init(dsn=str(settings.monitoring.SENTRY_DSN), enable_tracing=True)

app = FastAPI(
    title=settings.app.PROJECT_NAME,
    openapi_url=f"{settings.app.API_V1_STR}/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
)

# Set all CORS enabled origins
if settings.cors.all_cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors.all_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.app.API_V1_STR)