from typing import Generic, TypeVar, Optional
from pydantic import BaseModel
from .FieldErrorInternalModel import FieldErrorInternalModel

T = TypeVar("T")


class NoBianResponseModel(BaseModel, Generic[T]):
    Response: Optional[T] = None
    Errors: Optional[list[FieldErrorInternalModel]] = None
