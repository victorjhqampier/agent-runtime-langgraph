from pydantic import BaseModel, ConfigDict, Field


class UserContext(BaseModel):
    model_config = ConfigDict(extra="forbid")
    user_id: str = Field(min_length=1, description="Identificador único del usuario autenticado.")
    tenant_id: str = Field(min_length=1, description="Identificador del tenant/organización del usuario.")
    roles: list[str] = Field(default_factory=list, description="Roles asignados al usuario.")
    scopes: list[str] = Field(default_factory=list, description="Alcances o permisos del usuario.")
