from typing import Any
from pydantic import BaseModel, ConfigDict, Field
from Runtime.UseCases.AttendIncident.Schemas.RuntimeResponse import RuntimeResponse

class AgentRuntimeResponseModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str
    response_text: str
    citations: list[Any] = Field(default_factory=list)
    ticket: Any | None = None
    interrupt: Any | None = None
    voice_directives: Any | None = None
