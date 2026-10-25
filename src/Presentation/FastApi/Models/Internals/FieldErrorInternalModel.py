from pydantic import BaseModel, Field
from typing import Optional


class FieldErrorInternalModel(BaseModel):
    StatusCode: str
    Message: str
    Field: Optional[str] = Field(default=None, exclude=True)
