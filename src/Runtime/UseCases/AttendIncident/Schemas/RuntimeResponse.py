from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Citation(BaseModel):
    model_config = ConfigDict(extra="allow")

    document_id: str
    version: str | None = None
    section: str | None = None


class TicketResult(BaseModel):
    model_config = ConfigDict(extra="allow")

    ticket_id: str | None = None
    status: str


class InterruptResult(BaseModel):
    model_config = ConfigDict(extra="allow")

    type: str
    thread_id: str
    requested_fields: list[str] = Field(default_factory=list)


class VoiceDirectives(BaseModel):
    model_config = ConfigDict(extra="allow")

    language: str = "es-PE"
    tone: str = "professional"
    pace: str = "moderate"
    energy: str = "calm"
    formality: str = "professional"
    emphasis: list[str] = Field(default_factory=list)


class RuntimeResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["resolved", "needs_clarification", "escalated", "failed", "rejected"]
    response_text: str
    citations: list[Citation] = Field(default_factory=list)
    ticket: TicketResult | None = None
    interrupt: InterruptResult | None = None
    voice_directives: VoiceDirectives = Field(default_factory=VoiceDirectives)
