import asyncio
import logging
from typing import Dict, Optional, Any
from urllib.parse import quote
from Infrastructure.Tools.HttpClientHelper.Entities.HttpResponseEntity import HttpResponseEntity
from Infrastructure.Tools.HttpClientHelper.HttpClientConnector import HttpClientConnector
from Infrastructure.Tools.HttpClientHelper.HttpClientLogger import HttpClientLogger

# ********************************************************************************************************
# * Copyright © 2025 Arify Labs - All rights reserved.
# *
# * Info                  : Build a http request Handler.
# *
# * By                    : Victor Jhampier Caxi Maquera
# * Email/Mobile/Phone    : victorjhampier@gmail.com | 968991*14
# *
# * Creation date         : 03/01/2026
# *
# **********************************************************************************************************


class HttpClientBuilder:
    def __init__(self, http_connector: HttpClientConnector, logger: logging.Logger) -> None:
        self.__ApiClient: HttpClientConnector = http_connector
        self.__base_url: str = ""
        self.__endpoint: str = ""
        self.__headers: dict = {}
        self.__path_params: dict = {}
        self.__query: dict = {}
        self.__timeout: Optional[float] = None
        self._logger: logging.Logger = HttpClientLogger.set_logger().getChild(self.__class__.__name__)

    def timeout(self, timeout: float) -> "HttpClientBuilder":
        if timeout <= 0:
            raise ValueError("HTTP timeout must be positive.")
        self.__timeout = timeout
        return self

    def http(self, base_url: str) -> "HttpClientBuilder":
        self.__base_url = base_url.rstrip("/")
        return self

    def endpoint(self, endpoint: str) -> "HttpClientBuilder":
        self.__endpoint = endpoint.lstrip("/")
        return self

    def header(self, key: str, value: str) -> "HttpClientBuilder":
        self.__headers[key] = value
        return self

    def authorization(self, key: str, value: str) -> "HttpClientBuilder":
        # Método adicional, no en la interfaz
        self.__headers["Authorization"] = f"{key} {value}"
        return self

    def headers(self, headers: Dict[str, str]) -> "HttpClientBuilder":
        self.__headers.update(headers)
        return self

    def param(self, key: str, value: str) -> "HttpClientBuilder":
        self.__path_params[key] = value
        return self

    def params(self, params: Dict[str, str]) -> "HttpClientBuilder":
        self.__path_params.update(params)
        return self

    def query(self, key: str, value: str) -> "HttpClientBuilder":
        self.__query[key] = value
        return self

    def queries(self, queries: Dict[str, str]) -> "HttpClientBuilder":
        self.__query.update(queries)
        return self

    def _build_final_url(self) -> str:
        path = f"{self.__base_url}/{self.__endpoint}"

        # Path params: solo reemplazan placeholders dentro del path.
        # Se escapan con urllib.parse.quote para evitar caracteres especiales.
        for key, value in self.__path_params.items():
            placeholder = "{" + str(key) + "}"
            if placeholder not in path:
                raise ValueError(f"Path param '{key}' no tiene placeholder en endpoint. Use '{{{key}}}' o envíelo como query param.")
            path = path.replace(placeholder, quote(str(value), safe=""))

        return path

    def _ensure_default_headers(self) -> None:
        if not self.__headers:
            self.__headers["Content-Type"] = "application/json"

    async def get(self) -> HttpResponseEntity:
        return await self._send("GET")

    async def post(self, body: Optional[dict] = None) -> HttpResponseEntity:
        return await self._send("POST", body)

    async def put(self, body: Optional[dict] = None) -> HttpResponseEntity:
        return await self._send("PUT", body)

    async def _send(self, method: str, body: Optional[dict] = None) -> HttpResponseEntity:
        self._ensure_default_headers()
        final_url = ""

        try:
            final_url = self._build_final_url()
            response = await self.__ApiClient.request_async(
                method,
                final_url,
                json=body,
                params=self.__query,
                headers=self.__headers,
                timeout=self.__timeout,
            )
            return response
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            result = HttpResponseEntity(StatusCode=0, Content=None, Url=final_url)
            self._log_warning("HTTP request builder failed", "HttpClientBuilder._send", method, result.StatusCode, result.Url, body, str(exc))
            return result

    async def close(self) -> None:
        await self.__ApiClient.close()

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
