from pydantic import BaseModel

class ContextConfig(BaseModel):
    maximum_clarification_attempts: int = 2