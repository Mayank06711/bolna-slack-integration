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

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manages application lifecycle — startup and shutdown resources."""
    settings = get_settings()
    setup_logging(settings.log_level)

    logger.info(
        "Application starting",
        extra={"extra_data": {"env": settings.app_env, "port": settings.app_port}},
    )

    # Shared httpx client for outbound requests (Slack)
    app.state.http_client = httpx.AsyncClient(timeout=10.0)

    yield

    # Cleanup
    await app.state.http_client.aclose()
    logger.info("Application shutdown complete")


def create_app() -> FastAPI:
    """Application factory — builds and configures the FastAPI instance."""
    settings = get_settings()

    app = FastAPI(
        title="Bolna Slack Integration",
        description="Webhook server that sends Slack alerts when Bolna calls complete",
        version="1.0.0",
        lifespan=lifespan,
    )

    # Exception handlers
    app.add_exception_handler(WebhookProcessingError, webhook_processing_error_handler)
    app.add_exception_handler(SlackNotificationError, slack_notification_error_handler)
    app.add_exception_handler(DatabaseError, database_error_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    # Middleware (order matters — last added runs first)
    app.add_middleware(RequestLoggingMiddleware)

    if settings.enable_ip_whitelist:
        app.add_middleware(
            IPWhitelistMiddleware,
            allowed_ips=[settings.bolna_webhook_ip, "127.0.0.1"],
        )

    # Routes
    app.include_router(api_router)

    @app.get("/health")
    async def root_health():
        return {"status": "ok"}

    return app


app = create_app()
