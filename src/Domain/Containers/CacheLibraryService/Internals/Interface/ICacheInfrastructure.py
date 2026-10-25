from abc import ABC, abstractmethod
from datetime import timedelta
from typing import Any, Optional

from Domain.Containers.CacheLibraryService.Internals.CacheRecord import CacheRecord
from Domain.Containers.CacheLibraryService.Internals.CacheStatus import CacheStatus


class ICacheInfrastructure(ABC):
    @abstractmethod
    async def get_async(self, cache_id: str) -> Optional[CacheRecord[Any]]:
        pass

    @abstractmethod
    async def try_create_async(self, record: CacheRecord[Any], ttl: timedelta) -> bool:
        pass

    @abstractmethod
    async def try_update_async(self, record: CacheRecord[Any], expected_statuses: tuple[CacheStatus, ...], expected_owner: Optional[str], ttl: timedelta) -> bool:
        pass

    @abstractmethod
    async def remove_async(self, cache_id: str) -> bool:
        pass

    @abstractmethod
    async def try_remove_async(self, cache_id: str, expected_owner: Optional[str]) -> bool:
        pass

    @abstractmethod
    async def exists_async(self, cache_id: str) -> bool:
        pass
