import httpx

from app.models.schemas import CallAlertData
from app.core.logging import get_logger

logger = get_logger(__name__)

# Slack block text limit is 3000 chars, leaving room for ``` markers
MAX_CHUNK_LENGTH = 2800


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
                self._webhook_url, json=payload
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
        chunks = self._split_transcript(data.transcript)

        # Header blocks — call details
        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "Call Ended"},
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*ID:*\n`{data.id}`"},
                    {"type": "mrkdwn", "text": f"*Agent ID:*\n`{data.agent_id}`"},
                ],
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Duration:*\n{duration_formatted}"},
                ],
            },
            {"type": "divider"},
        ]

        # Transcript blocks — all chunks in one message so they stay together
        if len(chunks) == 1:
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Transcript:*\n```{chunks[0]}```"},
            })
        else:
            for i, chunk in enumerate(chunks, start=1):
                label = f"*Transcript ({i}/{len(chunks)}):*"
                blocks.append({
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"{label}\n```{chunk}```"},
                })

        return {
            "text": f"Call Ended | ID: {data.id} | Duration: {duration_formatted}",
            "blocks": blocks,
        }

    @staticmethod
    def _format_duration(seconds: float) -> str:
        minutes = int(seconds) // 60
        remaining = int(seconds) % 60
        return f"{minutes}m {remaining:02d}s"

    @staticmethod
    def _split_transcript(transcript: str) -> list[str]:
        if len(transcript) <= MAX_CHUNK_LENGTH:
            return [transcript]

        chunks = []
        remaining = transcript

        while remaining:
            if len(remaining) <= MAX_CHUNK_LENGTH:
                chunks.append(remaining)
                break

            # Break at last newline within limit to avoid cutting mid-sentence
            split_at = remaining.rfind("\n", 0, MAX_CHUNK_LENGTH)
            if split_at == -1:
                split_at = MAX_CHUNK_LENGTH

            chunks.append(remaining[:split_at])
            remaining = remaining[split_at:].lstrip("\n")

        return chunks
