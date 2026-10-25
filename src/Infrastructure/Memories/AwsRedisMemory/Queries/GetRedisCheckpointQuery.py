from typing import Any

from Infrastructure.Memories.AwsRedisMemory.RedisMemoryClient import RedisMemoryClient


class GetRedisCheckpointQuery:
    def __init__(self, client: RedisMemoryClient) -> None:
        self._client = client

    async def execute_async(self, thread_id: str) -> dict[str, Any] | None:
        return await self._client.get_async(thread_id)
