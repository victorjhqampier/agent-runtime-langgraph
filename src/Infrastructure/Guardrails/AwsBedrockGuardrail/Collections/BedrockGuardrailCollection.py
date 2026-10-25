from typing import Any, TypedDict


class BedrockGuardrailResultCollection(TypedDict, total=False):
    action: str
    outputs: list[dict[str, Any]]
    assessments: list[dict[str, Any]]
