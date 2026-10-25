import asyncio
import json
import sys
import unittest
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any, cast

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from Runtime.Adapters.RuntimeRequestAdapter import RuntimeRequestAdapter
from Runtime.Adapters.RuntimeResponseAdapter import RuntimeResponseAdapter
from Runtime.Internals.Executors.EasyAgentResult import EasyAgentResult
from Presentation.AmazonAgentcore.AmazonAgentcoreRuntime import AmazonAgentcoreRuntime


class StubUsecase:
    def __init__(self) -> None:
        self.request: RuntimeRequestAdapter | None = None

    async def execute_async(self, request: RuntimeRequestAdapter) -> EasyAgentResult[RuntimeResponseAdapter]:
        self.request = request
        return EasyAgentResult.success(
            RuntimeResponseAdapter(
                status="resolved",
                response_text="Incidente resuelto.",
                correlation_id=request.correlation_id,
                thread_id=request.thread_id,
            )
        )


class AmazonAgentcoreRuntimeTests(unittest.IsolatedAsyncioTestCase):
    def build_runtime(self, usecase: StubUsecase) -> AmazonAgentcoreRuntime:
        return AmazonAgentcoreRuntime(usecase_factory=cast(Callable[[], Any], lambda: usecase))

    def build_scope(self, method: str, path: str, headers: list[tuple[bytes, bytes]] | None = None) -> dict:
        return {"type": "http", "method": method, "path": path, "headers": headers or []}

    def build_receive(self, body: bytes = b""):
        messages = [{"type": "http.request", "body": body, "more_body": False}]

        async def receive() -> dict:
            return messages.pop(0)

        return receive

    def build_send(self) -> tuple[list[dict], Callable[[dict], Awaitable[None]]]:
        messages: list[dict] = []

        async def send(message: dict) -> None:
            messages.append(message)

        return messages, send

    async def test_ping_does_not_require_fastapi_or_runtime_services(self) -> None:
        runtime = self.build_runtime(StubUsecase())
        messages, send = self.build_send()

        await runtime(self.build_scope("GET", "/ping"), self.build_receive(), send)

        self.assertEqual(200, messages[0]["status"])
        self.assertEqual({"status": "Healthy"}, json.loads(messages[1]["body"]))

    async def test_invocation_maps_agentcore_http_request_to_runtime(self) -> None:
        usecase = StubUsecase()
        runtime = self.build_runtime(usecase)
        messages, send = self.build_send()
        payload = json.dumps({"session_id": "session-123", "conversation_id": "conversation-123", "message": "La VPN no conecta", "channel": "text"}).encode()
        headers = [
            (b"x-user-id", b"user-123"),
            (b"x-tenant-id", b"tenant-123"),
            (b"x-thread-id", b"thread-123"),
            (b"x-request-id", b"request-123"),
            (b"x-turn-id", b"turn-123"),
            (b"idempotency-key", b"idempotency-123"),
        ]

        await runtime.startup()
        await runtime(self.build_scope("POST", "/invocations", headers), self.build_receive(payload), send)

        self.assertEqual(200, messages[0]["status"])
        response = json.loads(messages[1]["body"])
        self.assertEqual("resolved", response["status"])
        self.assertIsNotNone(usecase.request)
        self.assertEqual("thread-123", usecase.request.thread_id if usecase.request else None)
        self.assertEqual("user-123", usecase.request.user_context.user_id if usecase.request else None)
        self.assertEqual("tenant-123", usecase.request.user_context.tenant_id if usecase.request else None)

    async def test_invocation_rejects_missing_trusted_identity_headers(self) -> None:
        runtime = self.build_runtime(StubUsecase())
        messages, send = self.build_send()
        payload = json.dumps({"session_id": "session-123", "conversation_id": "conversation-123", "message": "La VPN no conecta"}).encode()

        await runtime.startup()
        await runtime(self.build_scope("POST", "/invocations"), self.build_receive(payload), send)

        self.assertEqual(422, messages[0]["status"])
        self.assertEqual("rejected", json.loads(messages[1]["body"])["status"])

    async def test_runtime_supports_lifespan_without_fastapi(self) -> None:
        usecase = StubUsecase()
        runtime = self.build_runtime(usecase)
        messages: list[dict] = []
        lifecycle = [{"type": "lifespan.startup"}, {"type": "lifespan.shutdown"}]

        async def receive() -> dict:
            return lifecycle.pop(0)

        async def send(message: dict) -> None:
            messages.append(message)

        await runtime({"type": "lifespan"}, receive, send)

        self.assertEqual(["lifespan.startup.complete", "lifespan.shutdown.complete"], [message["type"] for message in messages])
        self.assertFalse(runtime.started)


if __name__ == "__main__":
    unittest.main()
