from pydantic import BaseModel, Field
from typing import Any
from uuid import UUID


class CostBreakdown(BaseModel):
    llm: float | None = Field(default=None)
    network: float | None = Field(default=None)
    platform: float | None = Field(default=None)
    synthesizer: float | None = Field(default=None)
    transcriber: float | None = Field(default=None)

    model_config = {"extra": "allow"}


class TelephonyData(BaseModel):
    duration: str | None = Field(default=None)
    to_number: str | None = Field(default=None)
    from_number: str | None = Field(default=None)
    call_type: str | None = Field(default=None)
    provider: str | None = Field(default=None)
    recording_url: str | None = Field(default=None)
    hosted_telephony: bool | None = Field(default=None)
    provider_call_id: str | None = Field(default=None)
    hangup_by: str | None = Field(default=None)
    hangup_reason: str | None = Field(default=None)
    hangup_provider_code: int | None = Field(default=None)
    ring_duration: int | None = Field(default=None)
    post_dial_delay: int | None = Field(default=None)
    to_number_carrier: str | None = Field(default=None)

    model_config = {"extra": "allow"}


class TransferCallData(BaseModel):
    provider_call_id: str | None = Field(default=None)
    status: str | None = Field(default=None)
    duration: str | None = Field(default=None)
    cost: float | None = Field(default=None)
    to_number: str | None = Field(default=None)
    from_number: str | None = Field(default=None)
    recording_url: str | None = Field(default=None)
    hangup_by: str | None = Field(default=None)
    hangup_reason: str | None = Field(default=None)
    hangup_provider_code: int | None = Field(default=None)

    model_config = {"extra": "allow"}


class BatchRunDetails(BaseModel):
    status: str | None = Field(default=None)
    created_at: str | None = Field(default=None)
    updated_at: str | None = Field(default=None)
    retried: int | None = Field(default=None)

    model_config = {"extra": "allow"}


class BolnaWebhookPayload(BaseModel):
    id: UUID = Field(...)
    agent_id: UUID = Field(...)
    status: str = Field(...)
    transcript: str | None = Field(default=None)
    conversation_time: float | None = Field(default=None)
    conversation_duration: float | None = Field(default=None)
    total_cost: float | None = Field(default=None)
    error_message: str | None = Field(default=None)
    answered_by_voice_mail: bool | None = Field(default=None)
    batch_id: str | None = Field(default=None)
    telephony_data: TelephonyData | None = Field(default=None)
    cost_breakdown: CostBreakdown | None = Field(default=None)
    transfer_call_data: TransferCallData | None = Field(default=None)
    batch_run_details: BatchRunDetails | None = Field(default=None)
    extracted_data: dict[str, Any] | None = Field(default=None)
    context_details: dict[str, Any] | None = Field(default=None)
    created_at: str | None = Field(default=None)
    updated_at: str | None = Field(default=None)

    model_config = {"extra": "allow"}


class CallAlertData(BaseModel):
    id: UUID
    agent_id: UUID
    duration: float
    transcript: str


class WebhookResponse(BaseModel):
    status: str
    message: str
