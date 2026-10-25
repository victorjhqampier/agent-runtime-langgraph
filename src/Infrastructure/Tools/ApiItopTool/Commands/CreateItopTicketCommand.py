from typing import Any

from Domain.Entities.Incident import Incident
from Domain.Entities.Ticket import Ticket
from Domain.Interfaces.Commands.ITicketCommand import ITicketCommand
from Infrastructure.Tools.ApiItopTool.ApiItopToolClient import ApiItopToolClient


class CreateItopTicketCommand(ITicketCommand):
    def __init__(self, client: ApiItopToolClient) -> None:
        self._client = client

    async def execute_async(self, payload: dict[str, Any], idempotency_key: str) -> dict[str, Any]:
        return await self._client.create_ticket_async(payload, idempotency_key)

    async def create_async(self, incident: Incident, idempotency_key: str) -> Ticket:
        payload = {
            "title": incident.description[:160],
            "description": incident.description,
            "tenant_id": incident.tenant_id.value,
            "session_id": incident.session_id,
            "conversation_id": incident.conversation_id,
            "category": incident.category,
            "priority": incident.priority.value,
        }
        response = await self.execute_async(payload, idempotency_key)
        ticket_id = str(response.get("ticket_id") or response.get("id") or response.get("number") or "").strip()
        status = str(response.get("status") or "created").strip()
        if not ticket_id:
            raise RuntimeError("iTop ticket creation was not confirmed")
        return Ticket(ticket_id=ticket_id, status=status)
