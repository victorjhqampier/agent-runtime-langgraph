from typing import Optional
from pydantic import BaseModel


class ValidationResultAdapter(BaseModel):
    Code: str
    Message: str
    Field: Optional[str]
