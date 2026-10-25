from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ThreadId:
    value: str

    def __post_init__(self) -> None:
        if not self.value or not self.value.strip():
            raise ValueError("Thread id cannot be empty")
