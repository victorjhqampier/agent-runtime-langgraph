from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Citation(BaseModel):
    """Referencia a un documento de evidencia autorizada usado en la respuesta.

    Permite rastrear qué documento del RAG sustentó cada afirmación del agente.
    """

    model_config = ConfigDict(extra="allow")

    document_id: str
    version: str | None = None
    section: str | None = None


class TicketResult(BaseModel):
    """Resultado de un ticket externo creado por el workflow.

    Solo se llena tras recibir confirmación real del sistema externo (iTop u otro).
    """

    model_config = ConfigDict(extra="allow")

    ticket_id: str | None = None
    status: str


class InterruptResult(BaseModel):
    """Información de interrupción cuando el workflow espera entrada del usuario.

    Indica el tipo de interrupción (clarification o ticket_confirmation), el `thread_id`
    para reanudar y los campos solicitados al usuario.
    """

    model_config = ConfigDict(extra="allow")

    type: str
    thread_id: str
    requested_fields: list[str] = Field(default_factory=list)


class VoiceDirectives(BaseModel):
    """Directivas de presentación para canales de voz.

    Solo modifican la presentación (idioma, tono, ritmo), nunca las reglas de negocio.
    """

    model_config = ConfigDict(extra="allow")

    language: str = "es-PE"
    tone: str = "professional"
    pace: str = "moderate"
    energy: str = "calm"
    formality: str = "professional"
    emphasis: list[str] = Field(default_factory=list)


class RuntimeResponse(BaseModel):
    """Respuesta final del caso de uso `attend_incident`.

    Contiene el estado semántico (resolved, needs_clarification, escalated, failed,
    rejected), el texto de respuesta, citas de evidencia, resultado de ticket (si aplica),
    interrupción (si está pausado) y directivas de voz. No usa códigos HTTP.
    """

    model_config = ConfigDict(extra="forbid")

    status: Literal["resolved", "needs_clarification", "escalated", "failed", "rejected"]
    response_text: str
    citations: list[Citation] = Field(default_factory=list)
    ticket: TicketResult | None = None
    interrupt: InterruptResult | None = None
    voice_directives: VoiceDirectives = Field(default_factory=VoiceDirectives)
