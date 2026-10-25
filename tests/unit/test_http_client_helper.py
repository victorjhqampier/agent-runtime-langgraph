import logging
import sys
import unittest
from pathlib import Path
from typing import Any, cast

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from Infrastructure.Tools.HttpClientHelper.HttpClientBuilder import HttpClientBuilder
from Infrastructure.Tools.HttpClientHelper.HttpClientConnector import HttpClientConnector


class FakeAsyncClient:
    def __init__(self, response: httpx.Response | None = None, exception: Exception | None = None) -> None:
        self._response = response
        self._exception = exception

    async def request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        if self._exception is not None:
            raise self._exception
        if self._response is None:
            raise AssertionError("FakeAsyncClient requires response or exception")
        return self._response

    async def aclose(self) -> None:
        return None


class HttpClientHelperTests(unittest.IsolatedAsyncioTestCase):
    def _connector_with_client(self, client: FakeAsyncClient) -> HttpClientConnector:
        connector = HttpClientConnector()
        connector._client = cast(Any, client)
        return connector

    def _response(self, status_code: int, content: bytes, content_type: str = "application/json", url: str = "https://example.test/users") -> httpx.Response:
        return httpx.Response(status_code, content=content, headers={"content-type": content_type}, request=httpx.Request("GET", url))

    async def test_200_with_json_dict_returns_content(self) -> None:
        connector = self._connector_with_client(FakeAsyncClient(response=self._response(200, b'{"ok": true}')))

        result = await connector.request_async("GET", "https://example.test/users")

        self.assertEqual(200, result.StatusCode)
        self.assertEqual({"ok": True}, result.Content)
        self.assertEqual("https://example.test/users", result.Url)

    async def test_200_with_html_returns_status_zero_and_warning(self) -> None:
        connector = self._connector_with_client(FakeAsyncClient(response=self._response(200, b"<html>bad</html>", "text/html")))

        with self.assertLogs("infrastructure.HttpClientConnector", level="WARNING") as logs:
            result = await connector.request_async("GET", "https://example.test/users")

        self.assertEqual(0, result.StatusCode)
        self.assertIsNone(result.Content)
        self.assertIn("HTTP response body is not valid JSON object", "\n".join(logs.output))

    async def test_200_with_json_list_returns_status_zero_and_warning(self) -> None:
        connector = self._connector_with_client(FakeAsyncClient(response=self._response(200, b"[]")))

        with self.assertLogs("infrastructure.HttpClientConnector", level="WARNING") as logs:
            result = await connector.request_async("GET", "https://example.test/users")

        self.assertEqual(0, result.StatusCode)
        self.assertIsNone(result.Content)
        self.assertIn("HTTP response body is not valid JSON object", "\n".join(logs.output))

    async def test_500_returns_status_and_warning(self) -> None:
        connector = self._connector_with_client(FakeAsyncClient(response=self._response(500, b'{"error": "failed"}')))

        with self.assertLogs("infrastructure.HttpClientConnector", level="WARNING") as logs:
            result = await connector.request_async("GET", "https://example.test/users")

        self.assertEqual(500, result.StatusCode)
        self.assertEqual({"error": "failed"}, result.Content)
        self.assertIn("HTTP request returned non-success status", "\n".join(logs.output))

    async def test_timeout_returns_408(self) -> None:
        request = httpx.Request("GET", "https://example.test/users")
        connector = self._connector_with_client(FakeAsyncClient(exception=httpx.ReadTimeout("timeout", request=request)))

        with self.assertLogs("infrastructure.HttpClientConnector", level="WARNING"):
            result = await connector.request_async("GET", "https://example.test/users")

        self.assertEqual(408, result.StatusCode)
        self.assertIsNone(result.Content)

    async def test_connection_error_returns_503(self) -> None:
        request = httpx.Request("GET", "https://example.test/users")
        connector = self._connector_with_client(FakeAsyncClient(exception=httpx.ConnectError("connection failed", request=request)))

        with self.assertLogs("infrastructure.HttpClientConnector", level="WARNING"):
            result = await connector.request_async("GET", "https://example.test/users")

        self.assertEqual(503, result.StatusCode)
        self.assertIsNone(result.Content)

    async def test_builder_missing_path_param_returns_status_zero(self) -> None:
        connector = self._connector_with_client(FakeAsyncClient(response=self._response(200, b'{"ok": true}')))
        http_client = HttpClientBuilder(connector, logging.getLogger("test"))
        http_client.http("https://example.test").endpoint("users").param("id", "123")

        with self.assertLogs("infrastructure.HttpClientBuilder", level="WARNING"):
            result = await http_client.get()

        self.assertEqual(0, result.StatusCode)
        self.assertIsNone(result.Content)

    def test_connector_respects_custom_connection_limits(self) -> None:
        connector = HttpClientConnector(max_connections=30, max_keepalive_connections=15, keepalive_expiry=60.0)

        transport = connector._client._transport
        self.assertIsInstance(transport, httpx.AsyncHTTPTransport)
        self.assertEqual(30, transport._pool._max_connections)
        self.assertEqual(15, transport._pool._max_keepalive_connections)
        self.assertEqual(60.0, transport._pool._keepalive_expiry)


if __name__ == "__main__":
    unittest.main()
