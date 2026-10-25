from pydantic import BaseModel
from .BianErrorInternalModel import BianErrorInternalModel


class BianResponseModel(BaseModel):
    errors: list[BianErrorInternalModel] | None = None
