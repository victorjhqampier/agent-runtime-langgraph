import asyncio
import httpx
from typing import Any, Optional

from Infrastructure.Tools.HttpClientHelper.Entities.HttpResponseEntity import HttpResponseEntity
from Infrastructure.Tools.HttpClientHelper.HttpClientLogger import HttpClientLogger


class HttpClientConnector:
    _MAX_LOG_BODY_LENGTH = 4096

    def __init__(
        self,
        timeout_sec: float = 5.0,
        connect_timeout_sec: float = 1.0,
        write_timeout_sec: float = 2.0,
        pool_timeout_sec: float = 1.0,
        retries: int = 0,
        max_connections: int = 30,
        max_keepalive_connections: int = 20,
        keepalive_expiry: float = 60.0,
    ) -> None:

        self._logger = HttpClientLogger.set_logger().getChild(self.__class__.__name__)
        limits = httpx.Limits(max_connections=max_connections, max_keepalive_connections=max_keepalive_connections, keepalive_expiry=keepalive_expiry)
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(connect=connect_timeout_sec, read=timeout_sec, write=write_timeout_sec, pool=pool_timeout_sec),
            http2=False,
            verify=True,
            transport=httpx.AsyncHTTPTransport(verify=True, retries=retries, limits=limits),
        )

    # -------------------------------------------------
    # 1. max_connections = 30
    # Puedo llegar a tener hasta 30 conexiones TCP
    # abiertas/en uso al mismo tiempo.
    # 2. max_keepalive_connections = 20
    # Cuando terminan las requests,
    # puedo conservar hasta 20 conexiones TCP abiertas
    # para reutilizarlas.
    # Las conexiones excedentes pueden cerrarse.
    # 3. keepalive_expiry = 90s (DNS, TCP TLS handshake)
    # De esas conexiones conservadas,
    # si una queda IDLE durante más de 90 segundos,
    # HTTPX la considera expirada y la cierra.
    # --------------------------------------------------
    async def close(self) -> None:
        await self._client.aclose()

    async def get_async(self, url: str, params=None, headers=None, timeout: Optional[float | httpx.Timeout] = None) -> HttpResponseEntity:
        return await self.request_async("GET", url, params=params, headers=headers, timeout=timeout)

    async def post_async(self, url: str, data=None, params=None, headers=None, timeout: Optional[float | httpx.Timeout] = None) -> HttpResponseEntity:
        return await self.request_async("POST", url, json=data, params=params, headers=headers, timeout=timeout)

    async def put_async(self, url: str, data=None, params=None, headers=None, timeout: Optional[float | httpx.Timeout] = None) -> HttpResponseEntity:
        return await self.request_async("PUT", url, json=data, params=params, headers=headers, timeout=timeout)

    async def request_async(self, method: str, url: str, *, json=None, params=None, headers=None, timeout: Optional[float | httpx.Timeout] = None) -> HttpResponseEntity:
        try:
            response = await self._client.request(method, url, json=json, params=params, headers=headers, timeout=timeout)
            result = self._build_response(response)
            response_body = result.Content if result.Content is not None else self._read_text_content(response)

            if result.StatusCode == 0:
                self._log_warning("HTTP response body is not valid JSON object", "HttpClientConnector.request_async", method, result.StatusCode, result.Url, json, response_body)
            elif result.StatusCode < 200 or result.StatusCode >= 300:
                self._log_warning("HTTP request returned non-success status", "HttpClientConnector.request_async", method, result.StatusCode, result.Url, json, response_body)

            return result
        except asyncio.CancelledError:
            self._logger.warning("HTTP request cancelled. Method=[%s] Url=[%s]", method, url)
            raise
        except httpx.TimeoutException as exc:
            result = HttpResponseEntity(StatusCode=408, Content=None, Url=url)
            self._log_warning("HTTP request timed out", "HttpClientConnector.request_async", method, result.StatusCode, result.Url, json, str(exc))
            return result
        except httpx.RequestError as exc:
            result = HttpResponseEntity(StatusCode=503, Content=None, Url=url)
            self._log_warning("HTTP request failed", "HttpClientConnector.request_async", method, result.StatusCode, result.Url, json, str(exc))
            return result
        except Exception as exc:
            result = HttpResponseEntity(StatusCode=500, Content=None, Url=url)
            self._log_warning("HTTP request failed unexpectedly", "HttpClientConnector.request_async", method, result.StatusCode, result.Url, json, str(exc))
            return result

    def _build_response(self, response: httpx.Response) -> HttpResponseEntity:
        content = self._read_json_content(response)
        status_code = 0 if response.status_code == 200 and content is None else response.status_code

        return HttpResponseEntity(
            StatusCode=status_code,
            Content=content,
            Url=str(response.url),
        )

    @staticmethod
    def _read_json_content(response: httpx.Response) -> Optional[dict]:
        content_type = response.headers.get("content-type", "")
        if not response.content or "json" not in content_type.lower():
            return None

        try:
            content = response.json()
            return content if isinstance(content, dict) else None
        except ValueError:
            return None

    def _read_text_content(self, response: httpx.Response) -> Optional[str]:
        if not response.content:
            return None

        content = response.text
        if len(content) <= self._MAX_LOG_BODY_LENGTH:
            return content
        return content[: self._MAX_LOG_BODY_LENGTH] + "...[truncated]"

    def _log_warning(self, message: str, operation: str, method: str, status_code: int, url: str, request_body: Any, response_body: Any) -> None:
        self._logger.warning(
            message,
            extra={
                "payload": {
                    "operation": operation,
                    "method": method,
                    "status_code": status_code,
                    "url": url,
                    "request_body": request_body,
                    "response_body": response_body,
                }
            },
        )
