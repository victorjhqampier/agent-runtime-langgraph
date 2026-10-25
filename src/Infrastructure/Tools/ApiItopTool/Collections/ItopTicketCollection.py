from typing import Any, TypedDict


class ItopTicketCollection(TypedDict, total=False):
    ticket_id: str
    status: str
    idempotency_key: str
    payload: dict[str, Any]
