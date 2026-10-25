import asyncio
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import StreamingResponse
from Presentation.BusinessApi.BusinessApiLogger import BusinessApiLogger


class ResponseTraceMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.logger = BusinessApiLogger.set_logger().getChild(self.__class__.__name__)

    async def dispatch(self, request, call_next):
        response = await call_next(request)

        if isinstance(response, StreamingResponse):
            body_parts: list[bytes] = []

            async def capture_stream():
                async for chunk in response.body_iterator:
                    body_chunk = chunk.encode("utf-8") if isinstance(chunk, str) else bytes(chunk)
                    body_parts.append(body_chunk)
                    yield body_chunk
                asyncio.create_task(self._log(str(request.url), b"".join(body_parts)))

            response.body_iterator = capture_stream()
        else:
            body = getattr(response, "body", b"")
            asyncio.create_task(self._log(str(request.url), body))

        return response

    async def _log(self, url, body):
        try:
            self.logger.info(f"RESPONSE - URL: {url}")
            self.logger.info(f"RESPONSE - Body: {body.decode('utf-8', errors='replace')}")
        except Exception:
            pass
