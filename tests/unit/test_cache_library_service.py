import asyncio
import sys
import unittest
from pathlib import Path
from datetime import timedelta
from typing import Any, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from Domain.Containers.CacheLibraryService.CacheLibraryService import CacheLibraryService
from Domain.Containers.CacheLibraryService.Internals.CacheRecord import CacheRecord
from Domain.Containers.CacheLibraryService.Internals.CacheStatus import CacheStatus
from Domain.Containers.CacheLibraryService.Internals.CacheStrategy import CacheStrategy
from Domain.Containers.CacheLibraryService.Internals.Interface.ICacheInfrastructure import ICacheInfrastructure
from Domain.Containers.CacheLibraryService.Internals.MemoryCacheInfrastructure import MemoryCacheInfrastructure


class FailingCacheProvider(ICacheInfrastructure):
    async def get_async(self, cache_id: str) -> Optional[CacheRecord[Any]]:
        raise ConnectionError("provider unavailable")

    async def try_create_async(self, record: CacheRecord[Any], ttl: timedelta) -> bool:
        raise ConnectionError("provider unavailable")

    async def try_update_async(self, record: CacheRecord[Any], expected_statuses: tuple[CacheStatus, ...], expected_owner: Optional[str], ttl: timedelta) -> bool:
        raise ConnectionError("provider unavailable")

    async def remove_async(self, cache_id: str) -> bool:
        raise ConnectionError("provider unavailable")

    async def try_remove_async(self, cache_id: str, expected_owner: Optional[str]) -> bool:
        raise ConnectionError("provider unavailable")

    async def exists_async(self, cache_id: str) -> bool:
        raise ConnectionError("provider unavailable")


class CancelledCacheProvider(FailingCacheProvider):
    async def get_async(self, cache_id: str) -> Optional[CacheRecord[Any]]:
        raise asyncio.CancelledError()


class CountingCacheProvider(ICacheInfrastructure):
    def __init__(self) -> None:
        self._inner = MemoryCacheInfrastructure()
        self.calls: dict[str, int] = {"get": 0, "create": 0, "update": 0, "remove": 0, "exists": 0}

    def reset_calls(self) -> None:
        for key in self.calls:
            self.calls[key] = 0

    async def get_async(self, cache_id: str) -> Optional[CacheRecord[Any]]:
        self.calls["get"] += 1
        return await self._inner.get_async(cache_id)

    async def try_create_async(self, record: CacheRecord[Any], ttl: timedelta) -> bool:
        self.calls["create"] += 1
        return await self._inner.try_create_async(record, ttl)

    async def try_update_async(self, record: CacheRecord[Any], expected_statuses: tuple[CacheStatus, ...], expected_owner: Optional[str], ttl: timedelta) -> bool:
        self.calls["update"] += 1
        return await self._inner.try_update_async(record, expected_statuses, expected_owner, ttl)

    async def remove_async(self, cache_id: str) -> bool:
        self.calls["remove"] += 1
        return await self._inner.remove_async(cache_id)

    async def try_remove_async(self, cache_id: str, expected_owner: Optional[str]) -> bool:
        self.calls["remove"] += 1
        return await self._inner.try_remove_async(cache_id, expected_owner)

    async def exists_async(self, cache_id: str) -> bool:
        self.calls["exists"] += 1
        return await self._inner.exists_async(cache_id)


class CacheLibraryServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_cache_only_is_fail_open_by_default(self) -> None:
        cache = CacheLibraryService(FailingCacheProvider())

        result = await cache.for_key("fail-open").use_strategy(CacheStrategy.CACHE_ONLY).resolve_async()

        self.assertIsNone(result)

    async def test_ensure_provider_available_raises_when_provider_fails(self) -> None:
        cache = CacheLibraryService(FailingCacheProvider())

        with self.assertRaises(RuntimeError):
            await cache.for_key("strict").ensure_provider_available().get_created_async()

    async def test_cache_only_required_raises_when_provider_fails(self) -> None:
        cache = CacheLibraryService(FailingCacheProvider())

        with self.assertRaises(RuntimeError):
            await cache.for_key("required").use_strategy(CacheStrategy.CACHE_ONLY_REQUIRED).resolve_async()

    async def test_provider_cancellation_is_not_swallowed(self) -> None:
        cache = CacheLibraryService(CancelledCacheProvider())

        with self.assertRaises(asyncio.CancelledError):
            await cache.for_key("cancelled").use_strategy(CacheStrategy.CACHE_ONLY).resolve_async()

    async def test_reserved_record_can_only_be_completed_by_same_owner(self) -> None:
        cache = CacheLibraryService(MemoryCacheInfrastructure())

        reserved = await cache.for_key("idempotency-key").with_owner("owner-a").try_reserve_async()
        no_owner_completed = await cache.for_key("idempotency-key").try_complete_async({"ok": True})
        wrong_owner_completed = await cache.for_key("idempotency-key").with_owner("owner-b").try_complete_async({"ok": True})
        right_owner_completed = await cache.for_key("idempotency-key").with_owner("owner-a").try_complete_async({"ok": True})
        value = await cache.for_key("idempotency-key").get_created_async()

        self.assertIsNotNone(reserved)
        self.assertFalse(no_owner_completed)
        self.assertFalse(wrong_owner_completed)
        self.assertTrue(right_owner_completed)
        self.assertEqual({"ok": True}, value)

    async def test_reserved_builder_is_returned_only_to_the_owner_that_acquires_the_key(self) -> None:
        cache = CacheLibraryService(MemoryCacheInfrastructure())

        reservation = await cache.for_key("idempotency-key").with_owner("owner-a").try_reserve_async()
        concurrent_reservation = await cache.for_key("idempotency-key").with_owner("owner-b").try_reserve_async()

        self.assertIsNotNone(reservation)
        self.assertIsNone(concurrent_reservation)

    async def test_unowned_reservation_cannot_be_completed_by_an_owner(self) -> None:
        cache = CacheLibraryService(MemoryCacheInfrastructure())

        await cache.for_key("idempotency-key").try_reserve_async()
        completed = await cache.for_key("idempotency-key").with_owner("owner-a").try_complete_async({"ok": True})

        self.assertFalse(completed)

    async def test_owner_can_update_a_created_record_with_try_complete_async(self) -> None:
        cache = CacheLibraryService(MemoryCacheInfrastructure())

        reservation = await cache.for_key("idempotency-key").with_owner("owner-a").try_reserve_async()
        first_completion = await reservation.try_complete_async({"version": 1}) if reservation is not None else False
        second_completion = await reservation.try_complete_async({"version": 2}) if reservation is not None else False
        value = await cache.for_key("idempotency-key").get_created_async()

        self.assertTrue(first_completion)
        self.assertTrue(second_completion)
        self.assertEqual({"version": 2}, value)

    async def test_other_owner_cannot_update_a_created_record_with_try_complete_async(self) -> None:
        cache = CacheLibraryService(MemoryCacheInfrastructure())

        reservation = await cache.for_key("idempotency-key").with_owner("owner-a").try_reserve_async()
        await reservation.try_complete_async({"version": 1}) if reservation is not None else False
        updated = await cache.for_key("idempotency-key").with_owner("owner-b").try_complete_async({"version": 2})
        value = await cache.for_key("idempotency-key").get_created_async()

        self.assertFalse(updated)
        self.assertEqual({"version": 1}, value)

    async def test_reserved_builder_can_only_remove_its_own_reservation(self) -> None:
        cache = CacheLibraryService(MemoryCacheInfrastructure())

        reservation = await cache.for_key("idempotency-key").with_owner("owner-a").try_reserve_async()
        wrong_owner_removed = await cache.for_key("idempotency-key").with_owner("owner-b").try_remove_async()
        right_owner_removed = await reservation.try_remove_async() if reservation is not None else False

        self.assertFalse(wrong_owner_removed)
        self.assertTrue(right_owner_removed)

    async def test_owned_created_record_can_be_closed_without_owner(self) -> None:
        cache = CacheLibraryService(MemoryCacheInfrastructure())

        await cache.for_key("preview-key").with_owner("owner-a").try_reserve_async()
        await cache.for_key("preview-key").with_owner("owner-a").try_complete_async({"preview": True})
        value = await cache.for_key("preview-key").use_strategy(CacheStrategy.CACHE_ONLY_THEN_CLOSE).resolve_async()
        status = await cache.for_key("preview-key").get_status_async()

        self.assertEqual({"preview": True}, value)
        self.assertEqual(CacheStatus.CLOSED, status)

    async def test_cache_then_source_and_store_miss_avoids_extra_provider_round_trips(self) -> None:
        provider = CountingCacheProvider()
        cache = CacheLibraryService(provider)

        async def loader() -> dict[str, bool]:
            return {"ok": True}

        value = await cache.for_key("cache-key").use_strategy(CacheStrategy.CACHE_THEN_SOURCE_AND_STORE).resolve_async(loader=loader)

        self.assertEqual({"ok": True}, value)
        self.assertEqual({"get": 1, "create": 1, "update": 1, "remove": 0, "exists": 0}, provider.calls)

    async def test_store_only_completes_started_record_without_extra_read(self) -> None:
        provider = CountingCacheProvider()
        cache = CacheLibraryService(provider)

        await cache.for_key("store-key").try_reserve_async()
        provider.reset_calls()
        completed = await cache.for_key("store-key").use_strategy(CacheStrategy.STORE_ONLY).put_async({"stored": True})

        self.assertTrue(completed)
        self.assertEqual({"get": 0, "create": 1, "update": 1, "remove": 0, "exists": 0}, provider.calls)


if __name__ == "__main__":
    unittest.main()
