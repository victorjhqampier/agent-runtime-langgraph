from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class BedrockLlmSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file="src/.env", extra="ignore", case_sensitive=True)

    provider: Literal["AWS_BEDROCK"] = Field(default="AWS_BEDROCK", validation_alias="RUNTIME_LLM_PROVIDER")
    region: str = Field(validation_alias="AWS_BEDROCK_LLM_REGION")
    model_id: str = Field(validation_alias="AWS_BEDROCK_LLM_MODEL_ID")
    temperature: float = Field(default=0.0, ge=0.0, le=2.0, validation_alias="AWS_BEDROCK_LLM_TEMPERATURE")
    max_tokens: int = Field(default=1200, gt=0, validation_alias="AWS_BEDROCK_LLM_MAX_TOKENS")
    connect_timeout_seconds: float = Field(default=5.0, gt=0, validation_alias="AWS_BEDROCK_LLM_CONNECT_TIMEOUT_SECONDS")
    read_timeout_seconds: float = Field(default=30.0, gt=0, validation_alias="AWS_BEDROCK_LLM_READ_TIMEOUT_SECONDS")
    max_attempts: int = Field(default=3, gt=0, validation_alias="AWS_BEDROCK_LLM_MAX_ATTEMPTS")
    max_pool_connections: int = Field(default=50, gt=0, validation_alias="AWS_BEDROCK_LLM_MAX_POOL_CONNECTIONS")
