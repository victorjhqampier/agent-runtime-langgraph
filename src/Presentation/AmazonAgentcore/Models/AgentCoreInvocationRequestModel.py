from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class AgentCoreInvocationRequestModel(BaseModel):
    """Payload accepted by the AgentCore Runtime HTTP protocol."""

    model_config = ConfigDict(extra="forbid")

    session_id: str = Field(min_length=1)
    conversation_id: str = Field(min_length=1)
    message: str = Field(min_length=1, max_length=20000)
    channel: Literal["text", "voice"] = "text"
    resume_input: dict[str, Any] | None = None
    turn_id: str | None = Field(default=None, min_length=1)
    correlation_id: str | None = Field(default=None, min_length=1)
    idempotency_key: str | None = Field(default=None, min_length=1)


class AgentCoreErrorModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    message: str
    field: str | None = None


class AgentCoreInvocationResponseModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str
    response_text: str
    citations: list[Any] = Field(default_factory=list)
    ticket: Any | None = None
    interrupt: Any | None = None
    voice_directives: Any | None = None
    correlation_id: str | None = None
    thread_id: str | None = None
    errors: list[AgentCoreErrorModel] = Field(default_factory=list)
