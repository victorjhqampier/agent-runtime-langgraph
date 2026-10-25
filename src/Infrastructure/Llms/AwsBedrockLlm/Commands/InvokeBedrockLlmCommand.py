import asyncio
import json
from typing import Any

import boto3
from botocore.config import Config

from Domain.Entities.Evidence import Evidence
from Domain.Entities.Incident import Incident
from Domain.Entities.IncidentAssessment import IncidentAssessment
from Domain.Enums.IncidentPriority import IncidentPriority
from Domain.Interfaces.Commands.IIncidentReasoningCommand import IIncidentReasoningCommand
from Infrastructure.Llms.AwsBedrockLlm.BedrockLlmSettings import BedrockLlmSettings


class InvokeBedrockLlmCommand(IIncidentReasoningCommand):
    def __init__(self, settings: BedrockLlmSettings) -> None:
        self._settings = settings
        self._client = boto3.client(
            "bedrock-runtime",
            region_name=settings.region,
            config=Config(
                retries={"total_max_attempts": settings.max_attempts, "mode": "adaptive"},
                connect_timeout=settings.connect_timeout_seconds,
                read_timeout=settings.read_timeout_seconds,
                max_pool_connections=settings.max_pool_connections,
            ),
        )

    async def converse_async(self, messages: list[dict[str, Any]], system: list[dict[str, Any]] | None = None, inference_config: dict[str, Any] | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "modelId": self._settings.model_id,
            "messages": messages,
            "inferenceConfig": inference_config or {"temperature": self._settings.temperature, "maxTokens": self._settings.max_tokens},
        }
        if system:
            payload["system"] = system
        return await asyncio.to_thread(self._client.converse, **payload)

    def get_text(self, response: dict[str, Any]) -> str:
        content = response.get("output", {}).get("message", {}).get("content", [])
        return "".join(str(item.get("text", "")) for item in content if isinstance(item, dict)).strip()

    def get_json(self, response: dict[str, Any]) -> dict[str, Any]:
        text = self.get_text(response)
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as error:
            raise ValueError("LLM analysis response is not valid JSON") from error
        if not isinstance(payload, dict):
            raise ValueError("LLM analysis response must be a JSON object")
        return payload

    async def analyze_async(
        self, incident: Incident, conversation_history: list[dict[str, str]], instructions: str, cancellation_event: asyncio.Event | None = None
    ) -> IncidentAssessment:
        if cancellation_event is not None and cancellation_event.is_set():
            raise asyncio.CancelledError
        response = await self.converse_async(
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "text": json.dumps(
                                {"incident": {"description": incident.description, "category": incident.category}, "conversation_history": conversation_history}, ensure_ascii=False
                            )
                        }
                    ],
                }
            ],
            system=[{"text": instructions}],
        )
        payload = self.get_json(response)
        in_scope = payload.get("in_scope") is True
        requires_clarification = payload.get("requires_clarification") is True
        clarification_question = str(payload.get("clarification_question") or "").strip() or None
        search_query = str(payload.get("search_query") or "").strip() or None
        if in_scope and not requires_clarification and search_query is None:
            requires_clarification = True
            clarification_question = "¿Podrías describir con más detalle el problema y el mensaje de error observado?"
        priority_value = str(payload.get("priority") or IncidentPriority.NORMAL.value).lower()
        priority = IncidentPriority(priority_value) if priority_value in {item.value for item in IncidentPriority} else IncidentPriority.NORMAL
        return IncidentAssessment(
            in_scope=in_scope,
            requires_clarification=requires_clarification,
            clarification_question=clarification_question,
            category=str(payload.get("category") or "").strip() or None,
            search_query=search_query,
            priority=priority,
        )

    async def generate_response_async(self, incident: Incident, evidence: list[Evidence], instructions: str, cancellation_event: asyncio.Event | None = None) -> str:
        if cancellation_event is not None and cancellation_event.is_set():
            raise asyncio.CancelledError
        response = await self.converse_async(
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "text": json.dumps(
                                {
                                    "incident": {"description": incident.description, "category": incident.category},
                                    "authorized_evidence": [
                                        {"document_id": item.document_id, "content": item.content, "version": item.version, "section": item.section} for item in evidence
                                    ],
                                },
                                ensure_ascii=False,
                            )
                        }
                    ],
                }
            ],
            system=[{"text": instructions}],
        )
        text = self.get_text(response)
        if not text:
            raise ValueError("LLM response is empty")
        return text
