from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class RedisMemorySettings(BaseSettings):
    model_config = SettingsConfigDict(env_file="src/.env", extra="ignore", case_sensitive=True)

    provider: str = Field(default="AWS_REDIS", validation_alias="RUNTIME_MEMORY_PROVIDER")
    host: str = Field(validation_alias="AWS_REDIS_MEMORY_HOST")
    port: int = Field(default=6379, gt=0, le=65535, validation_alias="AWS_REDIS_MEMORY_PORT")
    password: str | None = Field(default=None, validation_alias="AWS_REDIS_MEMORY_PASSWORD")
    database: int = Field(default=1, ge=0, validation_alias="AWS_REDIS_MEMORY_DB")
    ssl: bool = Field(default=False, validation_alias="AWS_REDIS_MEMORY_SSL")
    namespace: str = Field(default="agent-runtime", min_length=1, validation_alias="AWS_REDIS_MEMORY_NAMESPACE")
    ttl_seconds: int | None = Field(default=None, gt=0, validation_alias="AWS_REDIS_MEMORY_TTL_SECONDS")
    max_connections: int = Field(default=100, gt=0, validation_alias="AWS_REDIS_MEMORY_MAX_CONNECTIONS")
    socket_connect_timeout_seconds: float = Field(default=1.0, gt=0, validation_alias="AWS_REDIS_MEMORY_CONNECT_TIMEOUT_SECONDS")
    socket_timeout_seconds: float = Field(default=2.0, gt=0, validation_alias="AWS_REDIS_MEMORY_TIMEOUT_SECONDS")
