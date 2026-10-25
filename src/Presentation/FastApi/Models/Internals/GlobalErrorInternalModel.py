from pydantic import BaseModel


class GlobalErrorInternalModel(BaseModel):
    Code: str
    Message: str
