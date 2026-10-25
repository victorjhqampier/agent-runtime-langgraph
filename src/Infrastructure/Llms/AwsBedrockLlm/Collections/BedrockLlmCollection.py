from typing import Any, TypedDict


class BedrockLlmMessageCollection(TypedDict):
    role: str
    content: list[dict[str, Any]]
