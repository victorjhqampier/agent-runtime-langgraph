from langgraph.checkpoint.base import BaseCheckpointSaver

from Domain.Containers.DependencyInjection.CoreServices import CoreServices as Services
from Domain.Interfaces.Commands.IIncidentReasoningCommand import IIncidentReasoningCommand
from Domain.Interfaces.Commands.ITicketCommand import ITicketCommand
from Domain.Interfaces.Queries.IEvidenceQuery import IEvidenceQuery
from Domain.Interfaces.Queries.ITicketQuery import ITicketQuery
from Infrastructure.InfrastructureSetting import InfrastructureSetting
from Runtime.Ports.IRuntimeGraphPort import IRuntimeGraphPort
from Runtime.UseCases.AttendIncident.Workflows.AttendIncidentWorkflow import AttendIncidentWorkflow

# ********************************************************************************************************
# * Copyright © 2026 Arify Labs - All rights reserved.
# *
# * Info                  : Runtime services composition root and LangGraph workflow registration.
# *
# * By                    : Victor Jhampier Caxi Maquera
# * Email/Mobile/Phone    : victorjhampier@gmail.com | 968991*14
# *
# * Creation date         : 01/01/2026
# *
# **********************************************************************************************************

class CoreRuntimeSetting:
    @classmethod
    async def add_services(cls) -> None:
        await InfrastructureSetting.add_services()
        Services.add_singleton_factory(
            IRuntimeGraphPort,
            lambda: AttendIncidentWorkflow(
                Services.get_dependency(IIncidentReasoningCommand),
                Services.get_dependency(IEvidenceQuery),
                Services.get_dependency(ITicketCommand),
                Services.get_dependency(ITicketQuery),
                Services.get_dependency(BaseCheckpointSaver),
            ),
        )
