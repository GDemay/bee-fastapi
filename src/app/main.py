"""FastAPI application entry point."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.database import get_db_pool
from app.email.service import close_email_service, get_email_service
from app.exceptions import AppException
from app.users import router as users_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None]:
    settings = get_settings()
    db_pool = get_db_pool()

    logger.info("Starting application in %s mode", settings.app_env.value)
    logger.info(
        "Configuration - Debug: %s, Host: %s, Port: %s",
        settings.app_debug,
        settings.app_host,
        settings.app_port,
    )
    logger.info("Database URL: %s", settings.database_url.unicode_string().split("@")[-1])

    await db_pool.connect(settings)

    email_service = get_email_service()
    provider_name = email_service.provider.__class__.__name__
    logger.info("Email provider: %s", provider_name)

    yield

    logger.info("Shutting down application")
    await close_email_service()
    await db_pool.disconnect()


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="User Registration API",
        description="User registration with email verification",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.is_local else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(AppException)
    async def app_exception_handler(_: Request, exc: AppException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error_code": exc.error_code,
                "message": exc.message,
                "details": exc.details,
            },
        )

    @app.get("/health", tags=["health"])
    @app.get("/", tags=["health"])
    async def health_check() -> dict[str, str]:
        return {"status": "alive", "version": "1.0.0"}

    app.include_router(users_router)

    return app


app = create_app()
