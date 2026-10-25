from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class IncidentId:
    value: str

    def __post_init__(self) -> None:
        if not self.value or not self.value.strip():
            raise ValueError("Incident id cannot be empty")
