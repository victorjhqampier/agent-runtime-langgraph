from abc import ABC, abstractmethod

from Domain.Entities.Incident import Incident
from Domain.Entities.Ticket import Ticket


class ITicketCommand(ABC):
    @abstractmethod
    async def create_async(self, incident: Incident, idempotency_key: str) -> Ticket:
        pass
