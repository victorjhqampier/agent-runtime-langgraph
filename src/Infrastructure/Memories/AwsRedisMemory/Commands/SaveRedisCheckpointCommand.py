from typing import Any

from Infrastructure.Memories.AwsRedisMemory.RedisMemoryClient import RedisMemoryClient


class SaveRedisCheckpointCommand:
    def __init__(self, client: RedisMemoryClient) -> None:
        self._client = client

    async def execute_async(self, thread_id: str, checkpoint: dict[str, Any]) -> None:
        await self._client.save_async(thread_id, checkpoint)
