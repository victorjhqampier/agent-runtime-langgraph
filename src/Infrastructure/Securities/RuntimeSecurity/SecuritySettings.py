from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class SecuritySettings(BaseSettings):
    model_config = SettingsConfigDict(env_file="src/.env", extra="ignore", case_sensitive=True)

    pii_redaction_enabled: bool = Field(default=True, validation_alias="RUNTIME_SECURITY_PII_REDACTION_ENABLED")
    sensitive_value_mask: str = Field(default="[REDACTED]", validation_alias="RUNTIME_SECURITY_SENSITIVE_VALUE_MASK")
    checkpoint_minimization_enabled: bool = Field(default=True, validation_alias="RUNTIME_SECURITY_CHECKPOINT_MINIMIZATION_ENABLED")
