from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ApiItopToolSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file="src/.env", extra="ignore", case_sensitive=True)

    provider: Literal["ITOP"] = Field(default="ITOP", validation_alias="RUNTIME_TOOL_PROVIDER")
    base_url: str = Field(validation_alias="ITOP_TOOL_BASE_URL")
    create_ticket_path: str = Field(default="/api/tickets", validation_alias="ITOP_TOOL_CREATE_TICKET_PATH")
    lookup_idempotency_path: str = Field(default="/api/tickets/idempotency/{idempotency_key}", validation_alias="ITOP_TOOL_LOOKUP_IDEMPOTENCY_PATH")
    auth_mode: Literal["NONE", "BEARER", "BASIC"] = Field(default="BEARER", validation_alias="ITOP_TOOL_AUTH_MODE")
    auth_token: str | None = Field(default=None, validation_alias="ITOP_TOOL_AUTH_TOKEN")
    username: str | None = Field(default=None, validation_alias="ITOP_TOOL_USERNAME")
    password: str | None = Field(default=None, validation_alias="ITOP_TOOL_PASSWORD")
    timeout_seconds: float = Field(default=9.0, gt=0, validation_alias="ITOP_TOOL_TIMEOUT_SECONDS")
    connect_timeout_seconds: float = Field(default=3.0, gt=0, validation_alias="ITOP_TOOL_CONNECT_TIMEOUT_SECONDS")
    default_organization: str | None = Field(default=None, validation_alias="ITOP_TOOL_DEFAULT_ORGANIZATION")
    default_service: str | None = Field(default=None, validation_alias="ITOP_TOOL_DEFAULT_SERVICE")
