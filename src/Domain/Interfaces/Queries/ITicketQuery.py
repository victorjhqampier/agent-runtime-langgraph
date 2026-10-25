from abc import ABC, abstractmethod

from Domain.Entities.Ticket import Ticket


class ITicketQuery(ABC):
    @abstractmethod
    async def get_by_idempotency_async(self, idempotency_key: str) -> Ticket | None:
        pass
