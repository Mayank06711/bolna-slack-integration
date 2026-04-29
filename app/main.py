from contextlib import asynccontextmanager
from fastapi import FastAPI
import httpx

from app.config import get_settings
from app.core.logging import setup_logging, get_logger
from app.core.exceptions import (
    WebhookProcessingError,
    SlackNotificationError,
    DatabaseError,
    webhook_processing_error_handler,
    slack_notification_error_handler,
    database_error_handler,
    generic_exception_handler,
)
from app.middleware.request_logging import RequestLoggingMiddleware
from app.middleware.ip_whitelist import IPWhitelistMiddleware
from app.api.router import api_router
from app.core.database import get_db_manager

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    setup_logging(settings.log_level)

    logger.info(
        "Application starting",
        extra={"extra_data": {"env": settings.app_env, "port": settings.app_port}},
    )

    app.state.http_client = httpx.AsyncClient(timeout=10.0)

    db_manager = get_db_manager()
    db_connected = await db_manager.check_connection()
    logger.info(
        f"Database connection: {'established' if db_connected else 'FAILED'}",
        extra={"extra_data": {"db_connected": db_connected}},
    )

    yield

    await app.state.http_client.aclose()
    await db_manager.close()
    logger.info("Application shutdown complete")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Bolna Slack Integration",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_exception_handler(WebhookProcessingError, webhook_processing_error_handler)
    app.add_exception_handler(SlackNotificationError, slack_notification_error_handler)
    app.add_exception_handler(DatabaseError, database_error_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    app.add_middleware(RequestLoggingMiddleware)

    if settings.enable_ip_whitelist:
        app.add_middleware(
            IPWhitelistMiddleware,
            allowed_ips=[settings.bolna_webhook_ip, "127.0.0.1"],
        )

    app.include_router(api_router)

    @app.get("/health")
    async def root_health():
        return {"status": "ok"}

    return app


app = create_app()
