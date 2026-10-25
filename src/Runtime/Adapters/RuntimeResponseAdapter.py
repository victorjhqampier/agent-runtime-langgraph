from typing import Any, Literal
from pydantic import Field
from Runtime.UseCases.AttendIncident.Schemas.RuntimeResponse import Citation, InterruptResult, RuntimeResponse, TicketResult, VoiceDirectives


class RuntimeResponseAdapter(RuntimeResponse):
    """Canonical response contract returned independently of the transport."""

    status: Literal["resolved", "needs_clarification", "escalated", "failed", "rejected"] = Field(..., description="Semantic outcome of the Runtime execution.")
    response_text: str = Field(..., description="Textual response generated for the caller.")
    citations: list[Citation] = Field(default_factory=list, description="Authorized evidence references used by the response.")
    ticket: TicketResult | None = Field(default=None, description="Confirmed external ticket result, when one was created.")
    interrupt: InterruptResult | None = Field(default=None, description="Pending clarification or resume information.")
    voice_directives: VoiceDirectives = Field(default_factory=VoiceDirectives, description="Transport-neutral voice presentation instructions.")
    correlation_id: str = Field(..., min_length=1, description="Identifier that correlates the response with the Runtime execution.")
    thread_id: str = Field(..., min_length=1, description="Stable thread identifier used to continue the conversation.")

    @classmethod
    def from_graph_state(cls, state: dict[str, Any], thread_id: str, correlation_id: str) -> "RuntimeResponseAdapter":
        return cls(
            status=state.get("resolution_status", "failed"),
            response_text=state.get("response_text", ""),
            citations=state.get("citations", []),
            ticket=state.get("ticket"),
            interrupt=state.get("interrupt"),
            voice_directives=state.get("voice_directives", {}),
            correlation_id=correlation_id,
            thread_id=thread_id,
        )
