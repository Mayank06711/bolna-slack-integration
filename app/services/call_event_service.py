from sqlalchemy.ext.asyncio import AsyncSession

from app.models.schemas import BolnaWebhookPayload, CallAlertData
from app.models.database import CallLog
from app.core.logging import get_logger

logger = get_logger(__name__)

# Bolna fires webhooks on every status change (queued, ringing, in-progress, etc.)
# We only alert on "completed" — that's the final status after post-processing,
# when transcript and duration are fully available.
# "call-disconnected" fires first but often has incomplete transcript.
CALL_ENDED_STATUS = "completed"


class CallEventService:

    def process_webhook(self, payload: BolnaWebhookPayload) -> CallAlertData | None:
        logger.info(
            f"Processing webhook for execution {payload.id}",
            extra={"extra_data": {
                "execution_id": str(payload.id),
                "agent_id": str(payload.agent_id),
                "status": payload.status,
            }},
        )

        if payload.status != CALL_ENDED_STATUS:
            logger.info(
                f"Skipping status: {payload.status} — waiting for completed",
                extra={"extra_data": {
                    "execution_id": str(payload.id),
                    "status": payload.status,
                }},
            )
            return None

        duration = self._resolve_duration(payload)
        transcript = payload.transcript or ""

        alert_data = CallAlertData(
            id=payload.id,
            agent_id=payload.agent_id,
            duration=duration,
            transcript=transcript,
        )

        logger.info(
            "Call ended — extracted alert data",
            extra={"extra_data": {
                "execution_id": str(payload.id),
                "duration": duration,
                "transcript_length": len(transcript),
            }},
        )

        return alert_data

    async def save_call_log(
        self,
        payload: BolnaWebhookPayload,
        slack_notified: bool,
        session: AsyncSession,
    ) -> None:
        duration = self._resolve_duration(payload)

        call_log = CallLog(
            id=payload.id,
            agent_id=payload.agent_id,
            duration=duration,
            transcript=payload.transcript or "",
            status=payload.status,
            raw_payload=payload.model_dump(mode="json"),
            slack_notified=slack_notified,
        )

        session.add(call_log)
        await session.commit()

        logger.info(
            "Call log saved to database",
            extra={"extra_data": {
                "execution_id": str(payload.id),
                "slack_notified": slack_notified,
            }},
        )

    def _resolve_duration(self, payload: BolnaWebhookPayload) -> float:
        # Prefer telephony_data.duration (string of seconds from provider)
        # Fall back to conversation_time (float from Bolna)
        if payload.telephony_data and payload.telephony_data.duration:
            try:
                return float(payload.telephony_data.duration)
            except (ValueError, TypeError):
                pass

        return payload.conversation_time or 0.0
