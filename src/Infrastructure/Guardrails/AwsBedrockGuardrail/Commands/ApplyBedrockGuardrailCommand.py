import asyncio
from typing import Any, Literal

import boto3
from botocore.config import Config

from Infrastructure.Guardrails.AwsBedrockGuardrail.BedrockGuardrailSettings import BedrockGuardrailSettings


class ApplyBedrockGuardrailCommand:
    def __init__(self, settings: BedrockGuardrailSettings) -> None:
        self._settings = settings
        if settings.enabled and (not settings.region or not settings.guardrail_id or not settings.guardrail_version):
            raise ValueError("AWS_BEDROCK_GUARDRAIL_REGION, ID and VERSION are required when guardrails are enabled")
        self._client = None
        if settings.enabled:
            self._client = boto3.client(
                "bedrock-runtime",
                region_name=settings.region,
                config=Config(
                    retries={"total_max_attempts": settings.max_attempts, "mode": "adaptive"},
                    connect_timeout=settings.connect_timeout_seconds,
                    read_timeout=settings.read_timeout_seconds,
                ),
            )

    async def apply_async(self, text: str, source: Literal["INPUT", "OUTPUT"] = "INPUT") -> dict[str, Any]:
        if not self._settings.enabled:
            return {"action": "NONE", "outputs": [], "assessments": []}
        if self._client is None:
            raise RuntimeError("Bedrock Guardrail client is not initialized")
        return await asyncio.to_thread(
            self._client.apply_guardrail,
            guardrailIdentifier=self._settings.guardrail_id or "",
            guardrailVersion=self._settings.guardrail_version or "",
            source=source,
            content=[{"text": {"text": text}}],
        )
