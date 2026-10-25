from enum import Enum


class CacheStatus(str, Enum):
    STARTED = "started"
    CREATED = "created"
    CLOSED = "closed"
