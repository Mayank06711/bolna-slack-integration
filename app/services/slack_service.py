import httpx

from app.models.schemas import CallAlertData
from app.core.logging import get_logger

logger = get_logger(__name__)

# Slack block text limit is 3000 chars, leaving room for formatting (``` markers etc.)
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

        chunks = self._split_transcript(data.transcript)
        total_parts = len(chunks)

        # First message: header + call details + first transcript chunk
        first_payload = self._build_header_payload(data, chunks[0], total_parts)
        success = await self._post_to_slack(first_payload, data.id)
        if not success:
            return False

        # Remaining chunks as follow-up messages, linked by call ID
        for i, chunk in enumerate(chunks[1:], start=2):
            continuation_payload = self._build_continuation_payload(
                data.id, chunk, part=i, total=total_parts
            )
            success = await self._post_to_slack(continuation_payload, data.id)
            if not success:
                logger.error(
                    f"Failed to send transcript part {i}/{total_parts}",
                    extra={"extra_data": {"execution_id": str(data.id)}},
                )
                return False

        logger.info(
            f"Slack alert sent ({total_parts} message{'s' if total_parts > 1 else ''})",
            extra={"extra_data": {
                "execution_id": str(data.id),
                "transcript_parts": total_parts,
            }},
        )
        return True

    async def _post_to_slack(self, payload: dict, execution_id) -> bool:
        try:
            response = await self._http_client.post(
                self._webhook_url, json=payload
            )
            if response.status_code == 200:
                return True

            logger.error(
                f"Slack responded with {response.status_code}",
                extra={"extra_data": {
                    "execution_id": str(execution_id),
                    "status_code": response.status_code,
                    "response_body": response.text[:200],
                }},
            )
            return False

        except httpx.TimeoutException:
            logger.error(
                "Slack request timed out",
                extra={"extra_data": {"execution_id": str(execution_id)}},
            )
            return False
        except httpx.HTTPError as exc:
            logger.error(
                f"Slack HTTP error: {exc}",
                extra={"extra_data": {"execution_id": str(execution_id), "error": str(exc)}},
            )
            return False

    def _build_header_payload(self, data: CallAlertData, first_chunk: str, total_parts: int) -> dict:
        duration_formatted = self._format_duration(data.duration)
        transcript_label = "*Transcript:*" if total_parts == 1 else f"*Transcript (1/{total_parts}):*"

        return {
            "text": f"Call Ended | ID: {data.id} | Duration: {duration_formatted}",
            "blocks": [
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
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"{transcript_label}\n```{first_chunk}```"},
                },
            ],
        }

    def _build_continuation_payload(self, call_id, chunk: str, part: int, total: int) -> dict:
        return {
            "text": f"Transcript continued ({part}/{total}) for call {call_id}",
            "blocks": [
                {
                    "type": "context",
                    "elements": [
                        {"type": "mrkdwn", "text": f"*Transcript ({part}/{total})* | Call ID: `{call_id}`"},
                    ],
                },
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"```{chunk}```"},
                },
            ],
        }

    @staticmethod
    def _format_duration(seconds: float) -> str:
        minutes = int(seconds) // 60
        remaining = int(seconds) % 60
        return f"{minutes}m {remaining:02d}s"

    @staticmethod
    def _split_transcript(transcript: str) -> list[str]:
        # Split transcript into chunks that fit within Slack's block text limit
        # Breaks at newlines to avoid cutting mid-sentence
        if len(transcript) <= MAX_CHUNK_LENGTH:
            return [transcript]

        chunks = []
        remaining = transcript

        while remaining:
            if len(remaining) <= MAX_CHUNK_LENGTH:
                chunks.append(remaining)
                break

            # Find the last newline within the limit to avoid cutting mid-line
            split_at = remaining.rfind("\n", 0, MAX_CHUNK_LENGTH)
            if split_at == -1:
                # No newline found, hard cut at limit
                split_at = MAX_CHUNK_LENGTH

            chunks.append(remaining[:split_at])
            remaining = remaining[split_at:].lstrip("\n")

        return chunks
