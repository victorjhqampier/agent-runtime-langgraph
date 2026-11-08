"""Contexto de identidad del usuario para el caso de uso AttendIncident.

UserContext representa los datos de identidad y autorización del usuario que inicia
el incidente. Es validado por Presentation antes de llegar a Runtime y viaja dentro
del IncidentState como user_context.

Reglas para un junior:
- No incluir contraseñas, OTPs, tokens ni secretos en este modelo.
- user_id y tenant_id son obligatorios (min_length=1).
- extra="forbid" evita campos inesperados que puedan contener datos sensibles.
- Este contexto no modifica reglas de negocio; solo informa tenant y canal.
"""

from pydantic import BaseModel, ConfigDict, Field


class UserContext(BaseModel):
    """Datos de identidad y autorización del usuario.

    Proviene de Presentation (ya autenticado y autorizado). Runtime lo usa para
    construir el Incident y para el contexto del checkpointer.
    """

    model_config = ConfigDict(extra="forbid")

    user_id: str = Field(min_length=1, description="Identificador único del usuario autenticado.")
    tenant_id: str = Field(min_length=1, description="Identificador del tenant/organización del usuario.")
    roles: list[str] = Field(default_factory=list, description="Roles asignados al usuario.")
    scopes: list[str] = Field(default_factory=list, description="Alcances o permisos del usuario.")
