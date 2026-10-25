from typing import Any, TypedDict


class RedisCheckpointCollection(TypedDict):
    thread_id: str
    checkpoint: dict[str, Any]
