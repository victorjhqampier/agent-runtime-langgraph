from typing import Optional
from pydantic import BaseModel
from .FieldErrorInternalModel import FieldErrorInternalModel


class ResponseInternalModel(BaseModel):
    Errors: Optional[list[FieldErrorInternalModel]] = None
    Response: Optional[object] = None
