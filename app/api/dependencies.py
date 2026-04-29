from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.call_event_service import CallEventService
from app.services.slack_service import SlackNotificationService
from app.config import get_settings
from app.core.database import get_db_manager


def get_call_event_service() -> CallEventService:
    return CallEventService()


def get_slack_service(request: Request) -> SlackNotificationService:
    # Uses the shared httpx client created at app startup (connection reuse)
    settings = get_settings()
    http_client = request.app.state.http_client
    return SlackNotificationService(settings.slack_webhook_url, http_client)


async def get_db_session() -> AsyncSession:
    # Session is request-scoped — created here, closed after the request
    db_manager = get_db_manager()
    session = await db_manager.get_session()
    try:
        yield session
    finally:
        await session.close()
