from typing import Optional
from pydantic import BaseModel


class HttpResponseEntity(BaseModel):
    StatusCode: int
    Content: Optional[dict] = None
    Url: str
