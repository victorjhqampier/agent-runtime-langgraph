from pydantic import BaseModel


class BianErrorInternalModel(BaseModel):
    Status_code: str
    Message: str
