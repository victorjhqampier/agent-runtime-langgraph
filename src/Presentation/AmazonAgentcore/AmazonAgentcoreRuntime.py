import asyncio
import json
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from pydantic import ValidationError

from Domain.Containers.DependencyInjection.CoreServices import CoreServices as Services
from Presentation.AmazonAgentcore.Models.AgentCoreInvocationRequestModel import AgentCoreErrorModel, AgentCoreInvocationRequestModel, AgentCoreInvocationResponseModel
from Runtime.Adapters.RuntimeRequestAdapter import RuntimeRequestAdapter
from Runtime.Adapters.RuntimeResponseAdapter import RuntimeResponseAdapter
from Runtime.Internals.Executors.EasyAgentResult import EasyAgentResult
from Runtime.Ports.IRuntimeGraphPort import IRuntimeGraphPort
from Runtime.UseCases.AttendIncident.AttendIncidentUsecase import AttendIncidentUsecase
from Runtime.UseCases.AttendIncident.Schemas.ResumeInput import ResumeInput
from Runtime.UseCases.AttendIncident.Schemas.UserContext import UserContext
from Runtime.CoreRuntimeSetting import CoreRuntimeSetting

# ********************************************************************************************************
# * Copyright © 2026 Arify Labs - All rights reserved.
# *
# * Info                  : Amazon Bedrock AgentCore HTTP entrypoint for Agent Runtime.
# *
# * By                    : Victor Jhampier Caxi Maquera
# * Email/Mobile/Phone    : victorjhampier@gmail.com | 968991*14
# *
# * Creation date         : 01/01/2026
# *
# **********************************************************************************************************

class AmazonAgentcoreRuntime:
    REQUEST_TIMEOUT_SECONDS = 9.0

    def __init__(self, usecase_factory: Callable[[], AttendIncidentUsecase] | None = None, logger: logging.Logger | None = None) -> None:
        self.usecase_factory = usecase_factory
        self.usecase: AttendIncidentUsecase | None = None
        self.logger = logger or logging.getLogger("presentation.agentcore")
        self.started = False

    async def startup(self) -> None:
        if self.started:
            return
        if self.usecase_factory is None:
            await CoreRuntimeSetting.add_services()
            self.usecase = AttendIncidentUsecase(Services.get_dependency(IRuntimeGraphPort))
        else:
            self.usecase = self.usecase_factory()
        self.started = True

    async def shutdown(self) -> None:
        self.usecase = None
        self.started = False

    def get_header(self, headers: dict[bytes, bytes], name: str) -> str | None:
        value = headers.get(name.lower().encode("latin-1"))
        return value.decode("utf-8", errors="replace").strip() if value else None

    def get_required_header(self, headers: dict[bytes, bytes], name: str) -> str:
        value = self.get_header(headers, name)
        if not value:
            raise ValueError(f"Header {name} is required")
        return value

    def get_list_header(self, headers: dict[bytes, bytes], name: str) -> list[str]:
        value = self.get_header(headers, name) or ""
        return [item.strip() for item in value.split(",") if item.strip()]

    def build_user_context(self, headers: dict[bytes, bytes]) -> UserContext:
        return UserContext(
            user_id=self.get_required_header(headers, "x-user-id"),
            tenant_id=self.get_required_header(headers, "x-tenant-id"),
            roles=self.get_list_header(headers, "x-user-roles"),
            scopes=self.get_list_header(headers, "x-user-scopes"),
        )

    def build_runtime_request(self, body: AgentCoreInvocationRequestModel, headers: dict[bytes, bytes]) -> RuntimeRequestAdapter:
        thread_id = self.get_header(headers, "x-thread-id") or body.conversation_id
        correlation_id = self.get_header(headers, "x-request-id") or body.correlation_id or body.conversation_id
        turn_id = self.get_header(headers, "x-turn-id") or body.turn_id or correlation_id
        idempotency_key = self.get_header(headers, "idempotency-key") or body.idempotency_key or turn_id
        resume_input = ResumeInput(value=body.resume_input) if body.resume_input is not None else None
        return RuntimeRequestAdapter(
            session_id=body.session_id,
            conversation_id=body.conversation_id,
            thread_id=thread_id,
            correlation_id=correlation_id,
            turn_id=turn_id,
            message=body.message,
            channel=body.channel,
            user_context=self.build_user_context(headers),
            resume_input=resume_input,
            idempotency_key=idempotency_key,
        )

    def build_response(self, response: RuntimeResponseAdapter) -> AgentCoreInvocationResponseModel:
        return AgentCoreInvocationResponseModel(
            status=response.status,
            response_text=response.response_text,
            citations=response.citations,
            ticket=response.ticket,
            interrupt=response.interrupt,
            voice_directives=response.voice_directives,
            correlation_id=response.correlation_id,
            thread_id=response.thread_id,
        )

    def build_error_response(
        self, status: str, message: str, request: RuntimeRequestAdapter | None = None, errors: list[AgentCoreErrorModel] | None = None
    ) -> AgentCoreInvocationResponseModel:
        return AgentCoreInvocationResponseModel(
            status=status,
            response_text=message,
            correlation_id=request.correlation_id if request else None,
            thread_id=request.thread_id if request else None,
            errors=errors or [],
        )

    def build_validation_response(self, error: Exception) -> AgentCoreInvocationResponseModel:
        if isinstance(error, ValidationError):
            errors = [
                AgentCoreErrorModel(code="REQUEST_VALIDATION_ERROR", message=item.get("msg", "Invalid request."), field=".".join(str(part) for part in item.get("loc", ())) or None)
                for item in error.errors()
            ]
        else:
            errors = [AgentCoreErrorModel(code="REQUEST_VALIDATION_ERROR", message=str(error), field=None)]
        return self.build_error_response("rejected", "La solicitud contiene datos inválidos.", errors=errors)

    async def read_body(self, receive: Callable[[], Awaitable[dict[str, Any]]]) -> bytes:
        chunks: list[bytes] = []
        while True:
            message = await receive()
            if message["type"] != "http.request":
                continue
            chunks.append(message.get("body", b""))
            if not message.get("more_body", False):
                return b"".join(chunks)

    async def invoke(self, payload: bytes, headers: dict[bytes, bytes]) -> tuple[int, AgentCoreInvocationResponseModel]:
        try:
            body = AgentCoreInvocationRequestModel.model_validate_json(payload)
            request = self.build_runtime_request(body, headers)
        except (ValidationError, ValueError, TypeError) as error:
            return 422, self.build_validation_response(error)

        if self.usecase is None:
            return 500, self.build_error_response("failed", "El Runtime no está inicializado.", request)

        try:
            async with asyncio.timeout(self.REQUEST_TIMEOUT_SECONDS):
                result: EasyAgentResult[RuntimeResponseAdapter] = await self.usecase.execute_async(request)
            if not result.is_success or result.response is None:
                errors = [AgentCoreErrorModel(code=error.Code, message=error.Message, field=error.Field) for error in result.errors]
                return 422, self.build_error_response("rejected", "La solicitud fue rechazada por el Runtime.", request, errors)
            return 200, self.build_response(result.response)
        except asyncio.TimeoutError:
            self.logger.warning("AgentCore invocation timed out", extra={"thread_id": request.thread_id})
            return 408, self.build_error_response("failed", "La solicitud excedió el tiempo máximo de procesamiento.", request)
        except asyncio.CancelledError:
            self.logger.warning("AgentCore invocation cancelled", extra={"thread_id": request.thread_id})
            raise
        except Exception:
            self.logger.exception("AgentCore invocation failed", extra={"thread_id": request.thread_id})
            return 500, self.build_error_response("failed", "No fue posible completar la solicitud.", request)

    async def send_response(self, send: Callable[[dict[str, Any]], Awaitable[None]], status_code: int, response: AgentCoreInvocationResponseModel) -> None:
        payload = json.dumps(response.model_dump(exclude_none=True), ensure_ascii=False).encode("utf-8")
        await send(
            {"type": "http.response.start", "status": status_code, "headers": [(b"content-type", b"application/json"), (b"content-length", str(len(payload)).encode("ascii"))]}
        )
        await send({"type": "http.response.body", "body": payload})

    async def send_json(self, send: Callable[[dict[str, Any]], Awaitable[None]], status_code: int, payload: dict[str, Any]) -> None:
        encoded_payload = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        await send(
            {
                "type": "http.response.start",
                "status": status_code,
                "headers": [(b"content-type", b"application/json"), (b"content-length", str(len(encoded_payload)).encode("ascii"))],
            }
        )
        await send({"type": "http.response.body", "body": encoded_payload})

    async def handle_http(self, scope: dict[str, Any], receive: Callable[[], Awaitable[dict[str, Any]]], send: Callable[[dict[str, Any]], Awaitable[None]]) -> None:
        path = scope.get("path", "")
        method = scope.get("method", "")
        headers = dict(scope.get("headers", []))
        if method == "GET" and path == "/ping":
            await self.send_json(send, 200, {"status": "Healthy"})
            return
        if method != "POST" or path != "/invocations":
            await self.send_response(send, 404, self.build_error_response("rejected", "Ruta no encontrada."))
            return
        status_code, response = await self.invoke(await self.read_body(receive), headers)
        await self.send_response(send, status_code, response)

    async def handle_lifespan(self, receive: Callable[[], Awaitable[dict[str, Any]]], send: Callable[[dict[str, Any]], Awaitable[None]]) -> None:
        while True:
            message = await receive()
            if message["type"] == "lifespan.startup":
                try:
                    await self.startup()
                    await send({"type": "lifespan.startup.complete"})
                except Exception as error:
                    self.logger.exception("AgentCore Runtime startup failed")
                    await send({"type": "lifespan.startup.failed", "message": str(error)})
                    return
            elif message["type"] == "lifespan.shutdown":
                await self.shutdown()
                await send({"type": "lifespan.shutdown.complete"})
                return

    async def __call__(self, scope: dict[str, Any], receive: Callable[[], Awaitable[dict[str, Any]]], send: Callable[[dict[str, Any]], Awaitable[None]]) -> None:
        if scope["type"] == "lifespan":
            await self.handle_lifespan(receive, send)
            return
        if scope["type"] == "http":
            await self.handle_http(scope, receive, send)
            return
        raise RuntimeError(f"Unsupported ASGI scope type: {scope['type']}")


application = AmazonAgentcoreRuntime()
