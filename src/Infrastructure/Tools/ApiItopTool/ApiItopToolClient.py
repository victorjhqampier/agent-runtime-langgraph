import base64
from typing import Any

from Infrastructure.Tools.HttpClientHelper.HttpClientBuilder import HttpClientBuilder
from Infrastructure.Tools.HttpClientHelper.HttpClientConnector import HttpClientConnector
from Infrastructure.Tools.HttpClientHelper.Entities.HttpResponseEntity import HttpResponseEntity
from Infrastructure.InfrastructureLogger import InfrastructureLogger
from Infrastructure.Tools.ApiItopTool.ApiItopToolSettings import ApiItopToolSettings


class ApiItopToolClient:
    def __init__(self, connector: HttpClientConnector, settings: ApiItopToolSettings) -> None:
        self._connector = connector
        self._settings = settings
        self._logger = InfrastructureLogger.set_logger().getChild(self.__class__.__name__)

    def _headers(self, idempotency_key: str | None = None) -> dict[str, str]:
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        if self._settings.auth_mode == "BEARER" and self._settings.auth_token:
            headers["Authorization"] = f"Bearer {self._settings.auth_token}"
        if self._settings.auth_mode == "BASIC" and self._settings.username and self._settings.password:
            credentials = f"{self._settings.username}:{self._settings.password}".encode("utf-8")
            headers["Authorization"] = f"Basic {base64.b64encode(credentials).decode('ascii')}"
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        return headers

    def _builder(self, endpoint: str, headers: dict[str, str]) -> HttpClientBuilder:
        return HttpClientBuilder(self._connector, self._logger).http(self._settings.base_url).endpoint(endpoint).headers(headers).timeout(self._settings.timeout_seconds)

    @staticmethod
    def _content_or_raise(response: HttpResponseEntity, operation: str) -> dict[str, Any]:
        if response.StatusCode < 200 or response.StatusCode >= 300 or not response.Content:
            raise RuntimeError(f"iTop operation failed: {operation}; status={response.StatusCode}; url={response.Url}")
        return response.Content

    async def get_ticket_by_idempotency_async(self, idempotency_key: str) -> dict[str, Any] | None:
        path = self._settings.lookup_idempotency_path.replace("{idempotency_key}", idempotency_key)
        response = await self._builder(path, self._headers(idempotency_key)).get()
        if response.StatusCode == 404:
            return None
        return self._content_or_raise(response, "get_ticket_by_idempotency")

    async def create_ticket_async(self, payload: dict[str, Any], idempotency_key: str) -> dict[str, Any]:
        response = await self._builder(self._settings.create_ticket_path, self._headers(idempotency_key)).post(payload)
        return self._content_or_raise(response, "create_ticket")

    async def ping_async(self) -> bool:
        response = await self._builder("", self._headers()).get()
        return 200 <= response.StatusCode < 300
