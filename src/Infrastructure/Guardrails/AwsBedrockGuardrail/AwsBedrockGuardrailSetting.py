from Domain.Containers.DependencyInjection.CoreServices import CoreServices as Services
from Infrastructure.Guardrails.AwsBedrockGuardrail.BedrockGuardrailSettings import BedrockGuardrailSettings
from Infrastructure.Guardrails.AwsBedrockGuardrail.Commands.ApplyBedrockGuardrailCommand import ApplyBedrockGuardrailCommand


class BedrockGuardrailSetting:
    @classmethod
    def add_services(cls) -> None:
        settings = BedrockGuardrailSettings()
        if settings.provider != "AWS_BEDROCK":
            raise ValueError("RUNTIME_GUARDRAIL_PROVIDER must be AWS_BEDROCK for BedrockGuardrailSetting")
        Services.add_singleton_instance(ApplyBedrockGuardrailCommand(settings))
