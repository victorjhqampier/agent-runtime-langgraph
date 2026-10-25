from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Evidence:
    document_id: str
    content: str
    version: str | None = None
    section: str | None = None
    authorized: bool = False
    current: bool = False

    def __post_init__(self) -> None:
        if not self.document_id or not self.document_id.strip():
            raise ValueError("Evidence document id cannot be empty")
        if not self.content or not self.content.strip():
            raise ValueError("Evidence content cannot be empty")

    @property
    def is_usable(self) -> bool:
        return self.authorized and self.current
