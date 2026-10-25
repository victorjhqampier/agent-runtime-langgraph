import asyncio
from typing import Any

import boto3
from botocore.config import Config

from Domain.Entities.Evidence import Evidence
from Domain.Entities.Incident import Incident
from Domain.Interfaces.Queries.IEvidenceQuery import IEvidenceQuery
from Infrastructure.Rags.AwsBedrockRag.BedrockRagSettings import BedrockRagSettings


class RetrieveBedrockKnowledgeQuery(IEvidenceQuery):
    def __init__(self, settings: BedrockRagSettings) -> None:
        self._settings = settings
        self._client = boto3.client(
            "bedrock-agent-runtime",
            region_name=settings.region,
            config=Config(
                retries={"total_max_attempts": settings.max_attempts, "mode": "adaptive"},
                connect_timeout=settings.connect_timeout_seconds,
                read_timeout=settings.read_timeout_seconds,
                max_pool_connections=settings.max_pool_connections,
            ),
        )

    async def retrieve_raw_async(self, query: str, filters: dict[str, Any] | None = None, number_of_results: int | None = None) -> dict[str, Any]:
        vector_search_configuration: dict[str, Any] = {
            "numberOfResults": number_of_results or self._settings.number_of_results,
            "overrideSearchType": self._settings.search_type,
        }
        if filters:
            vector_search_configuration["filter"] = filters
        return await asyncio.to_thread(
            self._client.retrieve,
            knowledgeBaseId=self._settings.knowledge_base_id,
            retrievalQuery={"text": query},
            retrievalConfiguration={"vectorSearchConfiguration": vector_search_configuration},
        )

    async def retrieve_async(self, incident: Incident) -> list[Evidence]:
        response = await self.retrieve_raw_async(incident.description)
        evidence: list[Evidence] = []
        for result in response.get("retrievalResults", []):
            if not isinstance(result, dict):
                continue
            metadata = result.get("metadata") if isinstance(result.get("metadata"), dict) else {}
            location = result.get("location") if isinstance(result.get("location"), dict) else {}
            s3_location = location.get("s3Location") if isinstance(location.get("s3Location"), dict) else {}
            document_id = str(metadata.get("document_id") or result.get("id") or s3_location.get("uri") or "").strip()
            content = str(result.get("content", {}).get("text") or "").strip()
            if not document_id or not content:
                continue
            evidence.append(
                Evidence(
                    document_id=document_id,
                    content=content,
                    version=str(metadata["version"]) if metadata.get("version") is not None else None,
                    section=str(metadata["section"]) if metadata.get("section") is not None else None,
                    authorized=metadata.get("authorized") is True,
                    current=metadata.get("current") is True,
                )
            )
        return evidence
