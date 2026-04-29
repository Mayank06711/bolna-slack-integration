import httpx

from app.models.schemas import CallAlertData
from app.core.logging import get_logger

logger = get_logger(__name__)

# Slack block text has a 3000 char limit, leaving room for formatting
MAX_TRANSCRIPT_LENGTH = 2900


class SlackNotificationService:

    def __init__(self, webhook_url: str, http_client: httpx.AsyncClient):
        self._webhook_url = webhook_url
        self._http_client = http_client

    async def send_call_alert(self, data: CallAlertData) -> bool:
        logger.info(
            "Building Slack alert message",
            extra={"extra_data": {"execution_id": str(data.id)}},
        )

        payload = self._build_slack_payload(data)

        try:
            response = await self._http_client.post(
                self._webhook_url,
                json=payload,
            )

            if response.status_code == 200:
                logger.info(
                    "Slack alert sent successfully",
                    extra={"extra_data": {
                        "execution_id": str(data.id),
                        "status_code": response.status_code,
                    }},
                )
                return True

            logger.error(
                f"Slack responded with {response.status_code}",
                extra={"extra_data": {
                    "execution_id": str(data.id),
                    "status_code": response.status_code,
                    "response_body": response.text[:200],
                }},
            )
            return False

        except httpx.TimeoutException:
            logger.error(
                "Slack request timed out",
                extra={"extra_data": {"execution_id": str(data.id)}},
            )
            return False
        except httpx.HTTPError as exc:
            logger.error(
                f"Slack HTTP error: {exc}",
                extra={"extra_data": {"execution_id": str(data.id), "error": str(exc)}},
            )
            return False

    def _build_slack_payload(self, data: CallAlertData) -> dict:
        duration_formatted = self._format_duration(data.duration)
        transcript = self._truncate_transcript(data.transcript)

        return {
            "text": f"Call Ended | ID: {data.id} | Duration: {duration_formatted}",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "Call Ended",
                    },
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*ID:*\n`{data.id}`",
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Agent ID:*\n`{data.agent_id}`",
                        },
                    ],
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Duration:*\n{duration_formatted}",
                        },
                    ],
                },
                {"type": "divider"},
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Transcript:*\n```{transcript}```",
                    },
                },
            ],
        }

    @staticmethod
    def _format_duration(seconds: float) -> str:
        minutes = int(seconds) // 60
        remaining = int(seconds) % 60
        return f"{minutes}m {remaining:02d}s"

    @staticmethod
    def _truncate_transcript(transcript: str) -> str:
        if len(transcript) <= MAX_TRANSCRIPT_LENGTH:
            return transcript
        return transcript[:MAX_TRANSCRIPT_LENGTH] + "\n... [truncated]"
