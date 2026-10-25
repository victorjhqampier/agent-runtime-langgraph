from dataclasses import dataclass

from Domain.Enums.IncidentPriority import IncidentPriority
from Domain.Enums.IncidentStatus import IncidentStatus
from Domain.ValueObjects.IncidentId import IncidentId
from Domain.ValueObjects.TenantId import TenantId


@dataclass(slots=True)
class Incident:
    id: IncidentId
    tenant_id: TenantId
    session_id: str
    conversation_id: str
    description: str
    status: IncidentStatus = IncidentStatus.OPEN
    priority: IncidentPriority = IncidentPriority.NORMAL
    category: str | None = None

    def __post_init__(self) -> None:
        if not self.session_id or not self.session_id.strip():
            raise ValueError("Incident session id cannot be empty")
        if not self.conversation_id or not self.conversation_id.strip():
            raise ValueError("Incident conversation id cannot be empty")
        if not self.description or not self.description.strip():
            raise ValueError("Incident description cannot be empty")

    def escalate(self) -> None:
        if self.status in {IncidentStatus.RESOLVED, IncidentStatus.CLOSED}:
            raise ValueError("Resolved or closed incidents cannot be escalated")
        self.status = IncidentStatus.ESCALATED
