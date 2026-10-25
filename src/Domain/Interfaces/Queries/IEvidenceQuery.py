from abc import ABC, abstractmethod

from Domain.Entities.Evidence import Evidence
from Domain.Entities.Incident import Incident


class IEvidenceQuery(ABC):
    @abstractmethod
    async def retrieve_async(self, incident: Incident) -> list[Evidence]:
        pass
