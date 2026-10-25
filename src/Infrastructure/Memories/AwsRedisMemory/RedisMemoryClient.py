import json
from typing import Any

import redis.asyncio as redis
from redis.asyncio.client import Redis as AsyncRedis

from Infrastructure.Memories.AwsRedisMemory.RedisMemorySettings import RedisMemorySettings


class RedisMemoryClient:
    def __init__(self, settings: RedisMemorySettings) -> None:
        self._settings = settings
        self._redis: AsyncRedis = redis.Redis(
            host=settings.host,
            port=settings.port,
            password=settings.password or None,
            db=settings.database,
            ssl=settings.ssl,
            decode_responses=True,
            max_connections=settings.max_connections,
            socket_connect_timeout=settings.socket_connect_timeout_seconds,
            socket_timeout=settings.socket_timeout_seconds,
            socket_keepalive=True,
            health_check_interval=30,
        )

    def _key(self, thread_id: str) -> str:
        if not thread_id or not thread_id.strip():
            raise ValueError("thread_id is required")
        return f"{self._settings.namespace}:checkpoint:{thread_id}"

    def get_async_redis_client(self) -> AsyncRedis:
        return self._redis

    async def get_async(self, thread_id: str) -> dict[str, Any] | None:
        value = await self._redis.get(self._key(thread_id))
        return json.loads(value) if value else None

    async def save_async(self, thread_id: str, checkpoint: dict[str, Any]) -> None:
        payload = json.dumps(checkpoint, ensure_ascii=False, separators=(",", ":"), default=str)
        if self._settings.ttl_seconds:
            await self._redis.set(self._key(thread_id), payload, ex=self._settings.ttl_seconds)
        else:
            await self._redis.set(self._key(thread_id), payload)

    async def delete_async(self, thread_id: str) -> None:
        await self._redis.delete(self._key(thread_id))

    async def ping_async(self) -> bool:
        ping_result: Any = self._redis.ping()
        return bool(await ping_result)

    async def close(self) -> None:
        await self._redis.aclose()
