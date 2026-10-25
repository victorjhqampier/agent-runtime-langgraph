from Domain.Interfaces.Commands.IIncidentReasoningCommand import IIncidentReasoningCommand
from Domain.Containers.DependencyInjection.CoreServices import CoreServices as Services
from Infrastructure.Llms.AwsBedrockLlm.BedrockLlmSettings import BedrockLlmSettings
from Infrastructure.Llms.AwsBedrockLlm.Commands.InvokeBedrockLlmCommand import InvokeBedrockLlmCommand


class BedrockLlmSetting:
    @classmethod
    def add_services(cls) -> None:
        settings = BedrockLlmSettings()
        if settings.provider != "AWS_BEDROCK":
            raise ValueError("RUNTIME_LLM_PROVIDER must be AWS_BEDROCK for BedrockLlmSetting")
        command = InvokeBedrockLlmCommand(settings)
        Services.add_singleton_instance(command)
        Services.add_singleton_factory(IIncidentReasoningCommand, lambda: command)
