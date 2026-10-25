from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class BedrockGuardrailSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file="src/.env", extra="ignore", case_sensitive=True)

    provider: Literal["AWS_BEDROCK"] = Field(default="AWS_BEDROCK", validation_alias="RUNTIME_GUARDRAIL_PROVIDER")
    enabled: bool = Field(default=True, validation_alias="AWS_BEDROCK_GUARDRAIL_ENABLED")
    region: str | None = Field(default=None, validation_alias="AWS_BEDROCK_GUARDRAIL_REGION")
    guardrail_id: str | None = Field(default=None, validation_alias="AWS_BEDROCK_GUARDRAIL_ID")
    guardrail_version: str | None = Field(default=None, validation_alias="AWS_BEDROCK_GUARDRAIL_VERSION")
    connect_timeout_seconds: float = Field(default=5.0, gt=0, validation_alias="AWS_BEDROCK_GUARDRAIL_CONNECT_TIMEOUT_SECONDS")
    read_timeout_seconds: float = Field(default=15.0, gt=0, validation_alias="AWS_BEDROCK_GUARDRAIL_READ_TIMEOUT_SECONDS")
    max_attempts: int = Field(default=2, gt=0, validation_alias="AWS_BEDROCK_GUARDRAIL_MAX_ATTEMPTS")
