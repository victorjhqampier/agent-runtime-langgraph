from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ResumeInput(BaseModel):
    """Entrada para reanudar un workflow de `attend_incident` interrumpido.

    Se usa cuando el cliente envía una respuesta tras un `interrupt()` (pausa por
    aclaración o confirmación de ticket). Permite continuar la ejecución desde el
    estado guardado por el checkpointer duradero, usando el mismo `thread_id`.
    """

    model_config = ConfigDict(extra="allow")

    value: dict[str, Any] = Field(default_factory=dict)
