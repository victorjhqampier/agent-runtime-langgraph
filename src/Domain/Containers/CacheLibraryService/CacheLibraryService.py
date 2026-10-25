import asyncio
import random
from collections.abc import Awaitable, Callable
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, TypeVar

from Domain.Containers.CacheLibraryService.Internals.CacheRecord import CacheRecord
from Domain.Containers.CacheLibraryService.Internals.CacheStatus import CacheStatus
from Domain.Containers.CacheLibraryService.Internals.CacheStrategy import CacheStrategy
from Domain.Containers.CacheLibraryService.Internals.Interface.ICacheInfrastructure import ICacheInfrastructure

T = TypeVar("T")
Deserializer = Callable[[Any], T] | type[T]

# ********************************************************************************************************
# * Copyright � 2026 Arify Labs - All rights reserved.
# *
# * Info                  : Pluglin to handle caching with different strategies and a Redis provider implementation.
# *
# * By                    : Victor Jhampier Caxi Maquera
# * Email/Mobile/Phone    : victorjhampier@gmail.com | 968991714
# *
# * Creation date         : 07/05/2026
# *
# **********************************************************************************************************/


class CacheLibraryService:
    __slots__ = ("_provider",)

    def __init__(self, provider: ICacheInfrastructure) -> None:
        if provider is None:
            raise ValueError("Cache provider cannot be None.")
        self._provider = provider

    def for_key(self, key: str) -> "CacheBuilder":
        if key is None or not key.strip():
            raise ValueError("Cache key cannot be empty.")
        return CacheBuilder(key, self._provider)


class CacheBuilder:
    __slots__ = ("_id", "_provider", "_strategy", "_ttl", "_ttl_jitter", "_provider_required", "_owner_token")

    DEFAULT_TTL = timedelta(minutes=5)
    PROVIDER_TIMEOUT = 1.0
    MINIMUM_TTL = timedelta(seconds=1)
    NO_JITTER = timedelta(0)

    def __init__(self, cache_id: str, provider: ICacheInfrastructure) -> None:
        self._id = cache_id
        self._provider = provider
        self._strategy = CacheStrategy.CACHE_THEN_SOURCE_AND_STORE
        self._ttl = self.DEFAULT_TTL
        self._ttl_jitter = self.NO_JITTER
        self._provider_required = False
        self._owner_token: Optional[str] = None

    def use_strategy(self, strategy: CacheStrategy) -> "CacheBuilder":
        self._strategy = strategy
        return self

    def ensure_provider_available(self, required: bool = True) -> "CacheBuilder":
        self._provider_required = required
        return self

    def with_owner(self, owner_token: str) -> "CacheBuilder":
        self._owner_token = owner_token if owner_token and owner_token.strip() else None
        return self

    def with_ttl(self, ttl: timedelta, ttl_jitter: timedelta = timedelta(0)) -> "CacheBuilder":
        if ttl is None or ttl <= timedelta(0):
            raise ValueError("TTL must be positive.")
        if ttl < self.MINIMUM_TTL:
            raise ValueError("TTL must be at least one second.")
        if ttl_jitter is None:
            ttl_jitter = self.NO_JITTER
        if ttl_jitter < timedelta(0):
            raise ValueError("TTL jitter cannot be negative.")
        if ttl_jitter > timedelta(0) and ttl_jitter >= ttl / 3:
            raise ValueError("TTL jitter must be lower than one third of TTL.")
        self._ttl = ttl
        self._ttl_jitter = ttl_jitter
        return self

    async def resolve_async(self, loader: Optional[Callable[[], Awaitable[Optional[T]]]] = None, deserializer: Optional[Deserializer[T]] = None) -> Optional[T]:
        if self._strategy == CacheStrategy.CACHE_ONLY:
            record = await self.read_record()
            if record is None or record.status != CacheStatus.CREATED:
                return None
            return self.deserialize(record.cached_data, deserializer)

        if self._strategy == CacheStrategy.CACHE_ONLY_REQUIRED:
            record = await self.read_record(required=True)
            if record is None or record.status != CacheStatus.CREATED:
                return None
            return self.deserialize(record.cached_data, deserializer)

        if self._strategy == CacheStrategy.CACHE_ONLY_THEN_CLOSE:
            record = await self.read_record()
            if record is None or record.status != CacheStatus.CREATED:
                return None
            closed = CacheRecord(id=record.id, status=CacheStatus.CLOSED, cached_data=record.cached_data, created_at=record.created_at, expire_in=record.expire_in)
            changed = await self.update_record(closed, (CacheStatus.CREATED,))
            return self.deserialize(record.cached_data, deserializer) if changed else None

        if self._strategy == CacheStrategy.CACHE_THEN_SOURCE:
            record = await self.read_record()
            if record is not None and record.status == CacheStatus.CREATED:
                return self.deserialize(record.cached_data, deserializer)
            return await self.require_loader(loader)()

        if self._strategy == CacheStrategy.CACHE_THEN_SOURCE_AND_STORE:
            deferred_loader = self.require_loader(loader)
            record = await self.read_record()
            if record is not None and record.status == CacheStatus.CREATED:
                return self.deserialize(record.cached_data, deserializer)
            if record is not None and record.status in (CacheStatus.STARTED, CacheStatus.CLOSED):
                return None

            reservation = await self.try_reserve_async()
            if reservation is None:
                concurrent = await self.read_record()
                if concurrent is not None and concurrent.status == CacheStatus.CREATED:
                    return self.deserialize(concurrent.cached_data, deserializer)
                return None

            try:
                value = await deferred_loader()
                if value is None:
                    await reservation.try_remove_async()
                    return None
                await reservation.try_complete_async(value)
                return value
            except Exception:
                await reservation.try_remove_async()
                raise

        if self._strategy == CacheStrategy.SOURCE_AND_STORE:
            value = await self.require_loader(loader)()
            if value is None:
                return None
            await self.store_created(value)
            return value

        raise ValueError(f"{self._strategy.value} is not compatible with resolve_async. Use put_async instead.")

    async def put_async(self, value: Any = None) -> bool:
        if self._strategy == CacheStrategy.STORE_ONLY:
            return await self.store_created(value)
        if self._strategy == CacheStrategy.STORE_ONLY_OR_RESERVE:
            return await self.reserve()
        raise ValueError(f"{self._strategy.value} is not compatible with put_async.")

    async def remove_async(self) -> bool:
        return await self.execute_provider(lambda: self._provider.remove_async(self._id), False)

    async def try_remove_async(self) -> bool:
        return await self.execute_provider(lambda: self._provider.try_remove_async(self._id, self._owner_token), False)

    # obligatorio que el proveedor responda, si no error
    async def exists_async(self) -> bool:
        return await self.execute_provider(lambda: self._provider.exists_async(self._id), False, required=True)

    async def get_created_async(self, deserializer: Optional[Deserializer[T]] = None, required: bool = False) -> Optional[T]:
        record = await self.read_record(required=required)
        if record is None or record.status != CacheStatus.CREATED:
            return None
        return self.deserialize(record.cached_data, deserializer)

    async def get_status_async(self, required: bool = False) -> Optional[CacheStatus]:
        record = await self.read_record(required=required)
        return None if record is None else record.status

    async def try_reserve_async(self) -> Optional["CacheBuilder"]:
        now = self.utc_now()
        ttl = self.effective_ttl()
        record = CacheRecord(
            id=self._id, status=CacheStatus.STARTED, cached_data=None, created_at=self.to_epoch(now), expire_in=self.to_epoch(now + ttl), owner_token=self._owner_token
        )
        return self if await self.create_record(record, ttl) else None

    async def try_complete_async(self, value: Any) -> bool:
        now = self.utc_now()
        ttl = self.effective_ttl()
        record = CacheRecord(
            id=self._id, status=CacheStatus.CREATED, cached_data=value, created_at=self.to_epoch(now), expire_in=self.to_epoch(now + ttl), owner_token=self._owner_token
        )
        expected_statuses = (CacheStatus.STARTED, CacheStatus.CREATED) if self._owner_token is not None else (CacheStatus.STARTED,)
        return await self.update_record(record, expected_statuses, expected_owner=self._owner_token)

    async def read_record(self, required: bool = False) -> Optional[CacheRecord[Any]]:
        return await self.execute_provider(lambda: self._provider.get_async(self._id), None, required=required)

    async def reserve(self) -> bool:
        now = self.utc_now()
        ttl = self.effective_ttl()
        record = CacheRecord(id=self._id, status=CacheStatus.STARTED, cached_data=None, created_at=self.to_epoch(now), expire_in=self.to_epoch(now + ttl), owner_token=None)
        return await self.create_record(record, ttl)

    async def store_created(self, value: Any) -> bool:
        now = self.utc_now()
        ttl = self.effective_ttl()
        record = CacheRecord(id=self._id, status=CacheStatus.CREATED, cached_data=value, created_at=self.to_epoch(now), expire_in=self.to_epoch(now + ttl), owner_token=None)
        if await self.create_record(record, ttl):
            return True
        return await self.update_record(record, (CacheStatus.STARTED,), expected_owner=None)

    async def create_record(self, record: CacheRecord[Any], ttl: timedelta) -> bool:
        return await self.execute_provider(lambda: self._provider.try_create_async(record, ttl), False)

    async def update_record(self, record: CacheRecord[Any], expected_statuses: tuple[CacheStatus, ...], expected_owner: Optional[str] = None) -> bool:
        ttl = self.remaining_ttl(record)
        if ttl <= timedelta(0):
            return False
        return await self.execute_provider(lambda: self._provider.try_update_async(record, expected_statuses, expected_owner, ttl), False)

    async def execute_provider(self, operation: Callable[[], Awaitable[T]], fallback: T, required: bool = False) -> T:
        try:
            return await asyncio.wait_for(operation(), timeout=self.PROVIDER_TIMEOUT)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            if required or self._provider_required:
                raise RuntimeError(f"Cache Provider is unavailable. CacheId=[{self._id}]") from exc
            return fallback

    def effective_ttl(self) -> timedelta:
        if self._ttl_jitter == self.NO_JITTER:
            return self._ttl
        jitter = self._ttl_jitter.total_seconds()
        ttl = self._ttl + timedelta(seconds=random.uniform(-jitter, jitter))
        return ttl if ttl >= self.MINIMUM_TTL else self.MINIMUM_TTL

    @staticmethod
    def remaining_ttl(record: CacheRecord[Any]) -> timedelta:
        return datetime.fromtimestamp(record.expire_in, tz=timezone.utc) - datetime.now(timezone.utc)

    @staticmethod
    def deserialize(value: Any, deserializer: Optional[Deserializer[T]]) -> Optional[T]:
        if value is None or deserializer is None:
            return value
        if isinstance(deserializer, type):
            if isinstance(value, deserializer):
                return value
            if isinstance(value, dict):
                return deserializer(**value)
            if isinstance(value, (list, tuple)):
                return deserializer(*value)
            return deserializer(value)
        return deserializer(value)

    @staticmethod
    def require_loader(loader: Optional[Callable[[], Awaitable[Optional[T]]]]) -> Callable[[], Awaitable[Optional[T]]]:
        if loader is None:
            raise ValueError("This cache strategy requires a deferred async loader.")
        return loader

    @staticmethod
    def utc_now() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def to_epoch(value: datetime) -> int:
        return int(value.timestamp())
