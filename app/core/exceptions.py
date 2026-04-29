from fastapi import Request
from fastapi.responses import JSONResponse
from app.core.logging import get_logger

logger = get_logger(__name__)


class WebhookProcessingError(Exception):
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class SlackNotificationError(Exception):
    def __init__(self, message: str, status_code: int = 502):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class DatabaseError(Exception):
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


async def webhook_processing_error_handler(
    request: Request, exc: WebhookProcessingError
) -> JSONResponse:
    logger.error(
        "Webhook processing failed",
        extra={"extra_data": {"error": exc.message, "path": str(request.url)}},
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": "error", "message": exc.message},
    )


async def slack_notification_error_handler(
    request: Request, exc: SlackNotificationError
) -> JSONResponse:
    logger.error(
        "Slack notification failed",
        extra={"extra_data": {"error": exc.message, "path": str(request.url)}},
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": "error", "message": exc.message},
    )


async def database_error_handler(
    request: Request, exc: DatabaseError
) -> JSONResponse:
    logger.error(
        "Database operation failed",
        extra={"extra_data": {"error": exc.message, "path": str(request.url)}},
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": "error", "message": exc.message},
    )


async def generic_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    logger.error(
        "Unhandled exception",
        extra={"extra_data": {"error": str(exc), "path": str(request.url)}},
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={"status": "error", "message": "Internal server error"},
    )
