from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.schemas import BolnaWebhookPayload, WebhookResponse
from app.services.call_event_service import CallEventService
from app.services.slack_service import SlackNotificationService
from app.api.dependencies import (
    get_call_event_service,
    get_slack_service,
    get_db_session,
)
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.post("/webhook", response_model=WebhookResponse)
async def bolna_webhook(
    payload: BolnaWebhookPayload,
    call_service: CallEventService = Depends(get_call_event_service),
    slack_service: SlackNotificationService = Depends(get_slack_service),
    session: AsyncSession = Depends(get_db_session),
) -> WebhookResponse:
    logger.info(
        f"Webhook received for execution {payload.id}",
        extra={"extra_data": {
            "execution_id": str(payload.id),
            "status": payload.status,
        }},
    )

    alert_data = call_service.process_webhook(payload)

    if alert_data is None:
        return WebhookResponse(
            status="skipped",
            message=f"Status '{payload.status}' does not require notification",
        )

    slack_sent = await slack_service.send_call_alert(alert_data)

    # DB failure should not block the webhook response — Slack alert is the priority
    try:
        await call_service.save_call_log(payload, slack_notified=slack_sent, session=session)
    except Exception as exc:
        logger.error(
            f"Failed to save call log: {exc}",
            extra={"extra_data": {"execution_id": str(payload.id), "error": str(exc)}},
        )

    if slack_sent:
        return WebhookResponse(status="ok", message="Slack alert sent and call logged")

    return WebhookResponse(status="partial", message="Call logged but Slack alert failed")
