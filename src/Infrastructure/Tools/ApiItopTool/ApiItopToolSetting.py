from Domain.Interfaces.Commands.ITicketCommand import ITicketCommand
from Domain.Interfaces.Queries.ITicketQuery import ITicketQuery
from Domain.Containers.DependencyInjection.CoreServices import CoreServices as Services
from Infrastructure.Tools.ApiItopTool.Commands.CreateItopTicketCommand import CreateItopTicketCommand
from Infrastructure.Tools.ApiItopTool.ApiItopToolClient import ApiItopToolClient
from Infrastructure.Tools.ApiItopTool.ApiItopToolSettings import ApiItopToolSettings
from Infrastructure.Tools.ApiItopTool.Queries.GetItopTicketByIdempotencyQuery import GetItopTicketByIdempotencyQuery
from Infrastructure.Tools.HttpClientHelper.HttpClientConnector import HttpClientConnector


class ApiItopToolSetting:
    @classmethod
    def add_services(cls) -> None:
        settings = ApiItopToolSettings()
        if settings.provider != "ITOP":
            raise ValueError("RUNTIME_TOOL_PROVIDER must be ITOP for ApiItopToolSetting")
        connector = Services.get_instance(HttpClientConnector)
        client = ApiItopToolClient(connector, settings)
        Services.add_singleton_instance(client)
        command = CreateItopTicketCommand(client)
        query = GetItopTicketByIdempotencyQuery(client)
        Services.add_singleton_instance(command)
        Services.add_singleton_factory(ITicketCommand, lambda: command)
        Services.add_singleton_instance(query)
        Services.add_singleton_factory(ITicketQuery, lambda: query)
