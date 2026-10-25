from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Ticket:
    ticket_id: str
    status: str

    def __post_init__(self) -> None:
        if not self.ticket_id or not self.ticket_id.strip():
            raise ValueError("Ticket id cannot be empty")
        if not self.status or not self.status.strip():
            raise ValueError("Ticket status cannot be empty")
