from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Generic, Optional, TypeVar

from Domain.Containers.CacheLibraryService.Internals.CacheStatus import CacheStatus

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class CacheRecord(Generic[T]):
    id: str
    status: CacheStatus
    cached_data: Optional[T]
    created_at: int
    expire_in: int
    owner_token: Optional[str] = None

    def is_expired(self, now: datetime | None = None) -> bool:
        current = now or datetime.now(timezone.utc)
        return self.expire_in <= int(current.timestamp())
