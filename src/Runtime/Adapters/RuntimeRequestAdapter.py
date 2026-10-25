from typing import Literal
from pydantic import BaseModel, ConfigDict, Field
from Runtime.UseCases.AttendIncident.Schemas.ResumeInput import ResumeInput
from Runtime.UseCases.AttendIncident.Schemas.UserContext import UserContext


class RuntimeRequestAdapter(BaseModel):
    """Canonical request contract shared by every Runtime entry point."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    session_id: str = Field(..., min_length=1, description="Channel session identifier.")
    conversation_id: str = Field(..., min_length=1, description="Logical conversation identifier.")
    thread_id: str = Field(..., min_length=1, description="Stable LangGraph checkpoint thread identifier.")
    correlation_id: str = Field(..., min_length=1, description="Identifier used to correlate one execution across adapters.")
    turn_id: str = Field(..., min_length=1, description="Identifier of the current conversation turn.")
    message: str = Field(..., min_length=1, max_length=20000, description="Normalized user message supplied to the Runtime.")
    channel: Literal["text", "voice"] = Field(default="text", description="Presentation channel requested by the caller.")
    user_context: UserContext = Field(..., description="Authenticated user, tenant, roles and scopes.")
    resume_input: ResumeInput | None = Field(default=None, description="Input used to resume a paused Runtime interruption.")
    idempotency_key: str | None = Field(default=None, min_length=1, description="Optional key used to make external actions idempotent.")

    def to_graph_input(self) -> dict[str, object]:
        return {
            "session_id": self.session_id,
            "conversation_id": self.conversation_id,
            "thread_id": self.thread_id,
            "correlation_id": self.correlation_id,
            "turn_id": self.turn_id,
            "user_message": self.message,
            "user_context": self.user_context.model_dump(),
            "channel": self.channel,
            "resume_input": self.resume_input.model_dump() if self.resume_input else None,
            "idempotency_key": self.idempotency_key,
        }
