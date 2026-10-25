from typing import Any
from fastapi import Request
from fastapi.encoders import jsonable_encoder
from Presentation.BusinessApi.BusinessApiLogger import BusinessApiLogger
from Presentation.BusinessApi.Models.RequestInputModel import RequestInputModel
from Domain.Entities.Internals.MicroserviceCallTraceEntity import MicroserviceCallTraceEntity
from Domain.Containers.MemoryEvents.MicroserviceCallMemoryQueue import MicroserviceCallMemoryQueue
from datetime import datetime
from uuid import uuid4


class MicroserviceTraceHandler:
    def __init__(self, container: MicroserviceCallMemoryQueue) -> None:
        self._container: MicroserviceCallMemoryQueue = container
        self._request_datetime: datetime = datetime.utcnow()
        self._logger = BusinessApiLogger.set_logger().getChild(self.__class__.__name__)

    async def push_success(self, request_data: RequestInputModel, response: Any, status_code: int) -> None:
        await self._capture_trace(request_data, response, status_code, is_error=False)

    async def push_error(self, request_data: RequestInputModel, error: Exception, status_code: int = 500) -> None:
        await self._capture_trace(request_data, error, status_code, is_error=True)

    async def _capture_trace(self, request_data: RequestInputModel, response_or_error: Any, status_code: int, is_error: bool = False) -> None:
        request = request_data.request
        operation_name = request_data.operation_name
        keyword = str(request_data.keyword)

        # Capturar información del request
        headers: dict[str, str] = dict(request.headers)
        trace_id: str = headers.get("message-identification", "")
        channel_id: str = headers.get("channel-identification", "")
        device_id: str = headers.get("device-identification", "")
        request_url = str(request.url.path)
        method = request.method

        # Capturar payload del request
        request_payload = None
        try:
            body_bytes = await request.body()
            if body_bytes:
                body_str = body_bytes.decode("utf-8", errors="replace")
                body_str = " ".join(body_str.split())  # Elimina saltos de línea y espacios extra
                request_payload = body_str[:1000] + "..." if len(body_str) > 1000 else body_str
        except Exception as e:
            self._logger.warning(f"Error capturando request body: {e}")
            request_payload = None

        # Procesar respuesta o error
        if is_error:
            error_message = str(response_or_error)
            if len(error_message) > 1000:
                error_message: str = error_message[:1000] + "..."
            response_payload: str = f"ERROR: {error_message}"
        else:
            try:
                response_payload = jsonable_encoder(response_or_error)
                response_str = str(response_payload)
                # Limitar tamaño del payload de respuesta
                if len(response_str) > 2000:
                    response_str = response_str[:2000] + "..."
                response_payload = response_str
            except Exception as e:
                self._logger.warning(f"Error serializando response: {e}")
                response_payload = str(response_or_error)

        trace_entity = MicroserviceCallTraceEntity(
            Identity=str(uuid4()),
            TraceId=trace_id,
            ChannelId=channel_id,
            DeviceId=device_id,
            Keyword=keyword,
            Method=method,
            MicroserviceName="BusinessAPI2.0",
            OperationName=operation_name,
            RequestUrl=request_url,
            RequestPayload=request_payload,
            RequestDatetime=self._request_datetime,
            ResponseStatusCode=status_code,
            ResponsePayload=response_payload,
            ResponseDatetime=datetime.utcnow(),
        )

        if not await self._container.try_push(trace_entity):
            self._logger.warning(f"[QUEUE FULL], API: {trace_entity.TraceId} {trace_entity.RequestUrl} {trace_entity.ResponsePayload}")
