import asyncio
import logging
from fastapi import APIRouter, Depends, Header, Security
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from Domain.Containers.DependencyInjection.CoreServices import CoreServices as Services
from Presentation.FastApi.FastApiLogger import FastApiLogger
from Presentation.FastApi.Handlers.CognitoAuthorizer import CognitoAuthorizer
from Presentation.FastApi.Models.AgentRuntime.AgentResumeInputModel import AgentResumeInputModelValidator
from Presentation.FastApi.Models.AgentRuntime.AgentRuntimeRequestModel import AgentRuntimeRequestModel, AgentRuntimeRequestModelValidator
from Presentation.FastApi.Models.AgentRuntime.AgentRuntimeResponseModel import AgentRuntimeResponseModel
from Presentation.FastApi.Models.AgentRuntime.AgentTraceRequestModel import AgentTraceRequestModel, AgentTraceRequestModelValidator
from Runtime.Adapters.RuntimeRequestAdapter import RuntimeRequestAdapter
from Runtime.Internals.Adapters.ValidationResultAdapter import ValidationResultAdapter
from Runtime.Internals.Executors.EasyAgentResult import EasyAgentResult
from Runtime.Internals.Executors.FluentValidationExecutor import FluentValidationExecutor
from Runtime.Ports.IRuntimeGraphPort import IRuntimeGraphPort
from Runtime.UseCases.AttendIncident.AttendIncidentUsecase import AttendIncidentUsecase
from Runtime.UseCases.AttendIncident.Schemas.ResumeInput import ResumeInput
from Runtime.UseCases.AttendIncident.Schemas.UserContext import UserContext

# ********************************************************************************************************
# * Copyright © 2026 Arify Labs - All rights reserved.
# *
# * Info                  : FastAPI controller for Example Agent Runtime incident attendance.
# *
# * By                    : Victor Jhampier Caxi Maquera
# * Email/Mobile/Phone    : victorjhampier@gmail.com | 968991714
# *
# * Creation date         : 25/10/2026
# *
# **********************************************************************************************************


class ExampleAgentRuntimeController:
    _REQUEST_TIMEOUT_SECONDS = 9.0

    def __init__(self) -> None:
        self.ApiRouter = APIRouter(tags=["ExampleAgentRuntime"])
        self._logger: logging.Logger = FastApiLogger.set_logger().getChild(self.__class__.__name__)
        self.register_routes()

    def register_routes(self) -> None:
        self.ApiRouter.post(
            "/attend-incident/create",
            response_model=AgentRuntimeResponseModel,
            responses={408: {"model": AgentRuntimeResponseModel}, 422: {"model": AgentRuntimeResponseModel}, 500: {"model": AgentRuntimeResponseModel}},
        )(self.attend_incident_async)

    @staticmethod
    def get_attend_incident_usecase() -> AttendIncidentUsecase:
        return AttendIncidentUsecase(Services.get_dependency(IRuntimeGraphPort))

    async def attend_incident_async(
        self,
        body: AgentRuntimeRequestModel,
        device_identifier: str | None = Header(default=None, title="ID dispositivo", description="Identificador del dispositivo"),
        message_identifier: str | None = Header(default=None, title="ID mensaje", description="Identificador del mensaje"),
        channel_identifier: str | None = Header(default=None, title="ID canal", description="Identificador del canal"),
        session_identifier: str | None = Header(default=None, title="ID sesión", description="Identificador de la sesión"),
        usecase: AttendIncidentUsecase = Depends(get_attend_incident_usecase),
        _: dict = Security(CognitoAuthorizer(), scopes=["openid"]),
    ) -> JSONResponse:
        trace = AgentTraceRequestModel(
            device_identifier=device_identifier,
            message_identifier=message_identifier,
            channel_identifier=channel_identifier,
            session_identifier=session_identifier,
        )

        try:
            validation = FluentValidationExecutor.execute(trace, AgentTraceRequestModelValidator)
            if validation:
                return self.validation_response(validation)

            validation = FluentValidationExecutor.execute(body, AgentRuntimeRequestModelValidator)
            if validation:
                return self.validation_response(validation)

            if body.ResumeInput is not None:
                validation = FluentValidationExecutor.execute(body.ResumeInput, AgentResumeInputModelValidator)
                if validation:
                    return self.validation_response(validation)

            request_adapter = RuntimeRequestAdapter(
                session_id=body.SessionId,
                conversation_id=body.ConversationId,
                thread_id=trace.session_identifier,
                correlation_id=trace.message_identifier,
                turn_id=trace.message_identifier,
                message=body.Message,
                channel=body.Channel,
                user_context=UserContext(user_id=trace.device_identifier, tenant_id=body.SessionId),
                resume_input=ResumeInput(value=body.ResumeInput.Value) if body.ResumeInput is not None else None,
                idempotency_key=trace.message_identifier,
            )

            async with asyncio.timeout(self._REQUEST_TIMEOUT_SECONDS):
                result: EasyAgentResult = await usecase.execute_async(request_adapter)

            if not result.is_success or result.response is None:
                return self.validation_response(result.errors)

            return JSONResponse(status_code=200, content=jsonable_encoder(result.response.model_dump()))

        except asyncio.TimeoutError:
            self._logger.warning("Agent Runtime request timed out", extra={"thread_id": trace.session_identifier})
            return JSONResponse(
                status_code=408, content=jsonable_encoder(AgentRuntimeResponseModel(status="failed", response_text="La solicitud excedió el tiempo máximo de procesamiento."))
            )
        except Exception:
            self._logger.exception("Agent Runtime request failed", extra={"thread_id": trace.session_identifier})
            return JSONResponse(status_code=500, content=jsonable_encoder(AgentRuntimeResponseModel(status="failed", response_text="No fue posible completar la solicitud.")))

    @staticmethod
    def validation_response(errors: list[ValidationResultAdapter]) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "status": "rejected",
                "response_text": "La solicitud contiene datos inválidos.",
                "errors": [{"code": error.Code, "message": error.Message, "field": error.Field} for error in errors],
            },
        )
