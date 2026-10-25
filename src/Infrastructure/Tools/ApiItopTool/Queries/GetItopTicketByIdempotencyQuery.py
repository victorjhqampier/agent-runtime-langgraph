from typing import Any

from Domain.Entities.Ticket import Ticket
from Domain.Interfaces.Queries.ITicketQuery import ITicketQuery
from Infrastructure.Tools.ApiItopTool.ApiItopToolClient import ApiItopToolClient


class GetItopTicketByIdempotencyQuery(ITicketQuery):
    def __init__(self, client: ApiItopToolClient) -> None:
        self._client = client

    async def execute_async(self, idempotency_key: str) -> dict[str, Any] | None:
        return await self._client.get_ticket_by_idempotency_async(idempotency_key)

    async def get_by_idempotency_async(self, idempotency_key: str) -> Ticket | None:
        response = await self.execute_async(idempotency_key)
        if response is None:
            return None
        ticket_id = str(response.get("ticket_id") or response.get("id") or response.get("number") or "").strip()
        status = str(response.get("status") or "created").strip()
        if not ticket_id:
            raise RuntimeError("iTop idempotency lookup did not return a ticket identifier")
        return Ticket(ticket_id=ticket_id, status=status)
