from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ResumeInput(BaseModel):
    model_config = ConfigDict(extra="allow")

    value: dict[str, Any] = Field(default_factory=dict)
