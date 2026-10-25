from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class BedrockRagSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file="src/.env", extra="ignore", case_sensitive=True)

    provider: Literal["AWS_BEDROCK"] = Field(default="AWS_BEDROCK", validation_alias="RUNTIME_RAG_PROVIDER")
    region: str = Field(validation_alias="AWS_BEDROCK_RAG_REGION")
    knowledge_base_id: str = Field(validation_alias="AWS_BEDROCK_RAG_KNOWLEDGE_BASE_ID")
    number_of_results: int = Field(default=5, gt=0, le=100, validation_alias="AWS_BEDROCK_RAG_NUMBER_OF_RESULTS")
    search_type: Literal["HYBRID", "SEMANTIC"] = Field(default="HYBRID", validation_alias="AWS_BEDROCK_RAG_SEARCH_TYPE")
    max_attempts: int = Field(default=2, gt=0, validation_alias="AWS_BEDROCK_RAG_MAX_ATTEMPTS")
    connect_timeout_seconds: float = Field(default=5.0, gt=0, validation_alias="AWS_BEDROCK_RAG_CONNECT_TIMEOUT_SECONDS")
    read_timeout_seconds: float = Field(default=15.0, gt=0, validation_alias="AWS_BEDROCK_RAG_READ_TIMEOUT_SECONDS")
    max_pool_connections: int = Field(default=50, gt=0, validation_alias="AWS_BEDROCK_RAG_MAX_POOL_CONNECTIONS")
