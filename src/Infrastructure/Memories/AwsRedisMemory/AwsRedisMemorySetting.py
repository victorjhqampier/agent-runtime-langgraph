import math

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.redis import AsyncRedisSaver

from Domain.Containers.DependencyInjection.CoreServices import CoreServices as Services
from Infrastructure.Memories.AwsRedisMemory.Commands.SaveRedisCheckpointCommand import SaveRedisCheckpointCommand
from Infrastructure.Memories.AwsRedisMemory.RedisMemoryClient import RedisMemoryClient
from Infrastructure.Memories.AwsRedisMemory.RedisMemorySettings import RedisMemorySettings
from Infrastructure.Memories.AwsRedisMemory.Queries.GetRedisCheckpointQuery import GetRedisCheckpointQuery


class RedisMemorySetting:
    @classmethod
    async def add_services(cls) -> None:
        settings = RedisMemorySettings()
        if settings.provider != "AWS_REDIS":
            raise ValueError("RUNTIME_MEMORY_PROVIDER must be AWS_REDIS for RedisMemorySetting")
        client = RedisMemoryClient(settings)
        ttl = {"default_ttl": max(1, math.ceil(settings.ttl_seconds / 60)), "refresh_on_read": True} if settings.ttl_seconds else None
        checkpointer = AsyncRedisSaver(
            redis_client=client.get_async_redis_client(),
            ttl=ttl,
            checkpoint_prefix=f"{settings.namespace}:langgraph:checkpoint",
            checkpoint_write_prefix=f"{settings.namespace}:langgraph:checkpoint-write",
        )
        Services.add_singleton_instance(client)
        Services.add_singleton_instance(checkpointer)
        Services.add_singleton_factory(BaseCheckpointSaver, lambda: checkpointer)
        Services.add_singleton_instance(SaveRedisCheckpointCommand(client))
        Services.add_singleton_instance(GetRedisCheckpointQuery(client))
        await checkpointer.asetup()
