from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from Presentation.FastApi.Models.AgentRuntime.AgentRuntimeResponseModel import AgentRuntimeErrorModel, AgentRuntimeResponseModel


async def handle_agent_runtime_request_validation(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = [
        AgentRuntimeErrorModel(
            code="REQUEST_VALIDATION_ERROR",
            message=error.get("msg", "Invalid request."),
            field=".".join(str(part) for part in error.get("loc", ()) if part not in {"body", "header"}) or None,
        )
        for error in exc.errors()
    ]
    response = AgentRuntimeResponseModel(status="rejected", response_text="La solicitud contiene datos inválidos.", errors=errors)
    return JSONResponse(status_code=422, content=response.model_dump(exclude_none=True))
