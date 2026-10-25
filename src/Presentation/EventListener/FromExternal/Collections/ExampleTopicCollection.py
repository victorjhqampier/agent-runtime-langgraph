from pydantic import BaseModel, Field


class ExampleTopicCollection(BaseModel):
    code: str = Field(..., alias="code")
    message: str = Field(..., alias="message")
