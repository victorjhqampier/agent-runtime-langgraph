import asyncio
from abc import ABC, abstractmethod

from Domain.Entities.Evidence import Evidence
from Domain.Entities.Incident import Incident
from Domain.Entities.IncidentAssessment import IncidentAssessment


class IIncidentReasoningCommand(ABC):
    @abstractmethod
    async def analyze_async(
        self, incident: Incident, conversation_history: list[dict[str, str]], instructions: str, cancellation_event: asyncio.Event | None = None
    ) -> IncidentAssessment:
        pass

    @abstractmethod
    async def generate_response_async(self, incident: Incident, evidence: list[Evidence], instructions: str, cancellation_event: asyncio.Event | None = None) -> str:
        pass
