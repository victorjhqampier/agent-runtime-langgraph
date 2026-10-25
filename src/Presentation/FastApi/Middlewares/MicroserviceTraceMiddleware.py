import asyncio
from starlette.middleware.base import BaseHTTPMiddleware
from Presentation.BusinessApi.BusinessApiLogger import BusinessApiLogger


class MicroserviceTraceMiddleware(BaseHTTPMiddleware):
    def __init__(self, app) -> None:
        super().__init__(app)
        self.logger = BusinessApiLogger.set_logger().getChild(self.__class__.__name__)

    async def dispatch(self, request, call_next):
        body = await request.body()

        async def receive():
            return {"type": "http.request", "body": body, "more_body": False}

        request._receive = receive

        asyncio.create_task(self._log(str(request.url), dict(request.headers), body))

        # Respuesta Obligatoria
        return await call_next(request)

    async def _log(self, url, headers, body) -> None:
        try:
            self.logger.info(f"REQUEST - URL: {url}")
            self.logger.info(f"REQUEST - Headers: {headers}")
            self.logger.info(f"REQUEST - Body: {body.decode('utf-8', errors='replace')}")
        except Exception:
            pass
