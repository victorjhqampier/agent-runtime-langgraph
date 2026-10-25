from dataclasses import dataclass
from fastapi import Request


@dataclass
class RequestInputModel:
    request: Request
    operation_name: str
    keyword: str
