from typing import Optional
from pydantic import BaseModel
from .BianErrorInternalModel import BianErrorInternalModel


class BianErrorResponseModel(BaseModel):
    errors: Optional[list[BianErrorInternalModel]] = None
