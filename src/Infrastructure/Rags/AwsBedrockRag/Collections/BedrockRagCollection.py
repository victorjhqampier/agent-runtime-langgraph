from typing import Any, TypedDict


class BedrockRetrievedDocumentCollection(TypedDict, total=False):
    document_id: str
    version: str
    section: str
    content: str
    source_uri: str
    metadata: dict[str, Any]
