import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from Domain.Containers.CacheLibraryService.Internals.CacheRecord import CacheRecord
from Domain.Containers.CacheLibraryService.Internals.CacheStatus import CacheStatus
from Domain.Containers.CacheLibraryService.Internals.Interface.ICacheInfrastructure import ICacheInfrastructure


class MemoryCacheInfrastructure(ICacheInfrastructure):
    __slots__ = ("_records", "_lock")

    def __init__(self) -> None:
        self._records: dict[str, CacheRecord[Any]] = {}
        self._lock = asyncio.Lock()

    async def get_async(self, cache_id: str) -> Optional[CacheRecord[Any]]:
        async with self._lock:
            record = self._records.get(cache_id)
            if record is None:
                return None
            if record.is_expired(datetime.now(timezone.utc)):
                self._records.pop(cache_id, None)
                return None
            return record

    async def try_create_async(self, record: CacheRecord[Any], ttl: timedelta) -> bool:
        async with self._lock:
            current = self._records.get(record.id)
            if current is not None and not current.is_expired(datetime.now(timezone.utc)):
                return False
            self._records[record.id] = record
            return True

    async def try_update_async(self, record: CacheRecord[Any], expected_statuses: tuple[CacheStatus, ...], expected_owner: Optional[str], ttl: timedelta) -> bool:
        async with self._lock:
            current = self._records.get(record.id)
            now = datetime.now(timezone.utc)
            if current is None:
                return False
            if current.is_expired(now):
                self._records.pop(record.id, None)
                return False
            if current.status not in expected_statuses:
                return False
            if CacheStatus.STARTED in expected_statuses and current.owner_token != expected_owner:
                return False
            self._records[record.id] = record
            return True

    async def remove_async(self, cache_id: str) -> bool:
        async with self._lock:
            return self._records.pop(cache_id, None) is not None

    async def try_remove_async(self, cache_id: str, expected_owner: Optional[str]) -> bool:
        async with self._lock:
            current = self._records.get(cache_id)
            if current is None:
                return False
            if current.is_expired(datetime.now(timezone.utc)):
                self._records.pop(cache_id, None)
                return False
            if current.owner_token != expected_owner:
                return False
            self._records.pop(cache_id, None)
            return True

    async def exists_async(self, cache_id: str) -> bool:
        return await self.get_async(cache_id) is not None
