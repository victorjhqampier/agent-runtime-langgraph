from enum import Enum


class CacheStrategy(str, Enum):
    CACHE_ONLY = "cache_only"
    CACHE_ONLY_REQUIRED = "cache_only_required"
    CACHE_ONLY_THEN_CLOSE = "cache_only_then_close"
    CACHE_THEN_SOURCE = "cache_then_source"
    CACHE_THEN_SOURCE_AND_STORE = "cache_then_source_and_store"
    SOURCE_AND_STORE = "source_and_store"
    STORE_ONLY = "store_only"
    STORE_ONLY_OR_RESERVE = "store_only_or_reserve"
