import operator
from typing import Annotated, Any, Literal

from typing_extensions import TypedDict


class IncidentState(TypedDict, total=False):
    session_id: str
    conversation_id: str
    thread_id: str
    correlation_id: str
    turn_id: str
    user_message: str
    conversation_history: Annotated[list[dict[str, str]], operator.add]
    sanitized_message: str
    user_context: dict[str, Any]
    channel: Literal["text", "voice"]
    resume_input: dict[str, Any] | None
    classification: dict[str, Any]
    conversation_signal: dict[str, Any]
    search_query: str
    search_attempts: int
    retrieved_documents: list[dict[str, Any]]
    evidence_status: Literal["unknown", "sufficient", "insufficient", "unauthorized"]
    evidence_reason: str
    citations: list[dict[str, Any]]
    clarification_attempts: int
    ticket_confirmation: Literal["pending", "confirmed", "declined", "not_required"]
    resolution_status: Literal["pending", "resolved", "needs_clarification", "escalated", "failed", "rejected"]
    ticket: dict[str, Any] | None
    response_text: str
    interrupt: dict[str, Any] | None
    voice_directives: dict[str, Any]
