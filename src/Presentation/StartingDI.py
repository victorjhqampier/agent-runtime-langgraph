from Domain.Containers.DependencyInjection.CoreServices import CoreServices as Services
from Runtime.Ports.IRuntimeGraphPort import IRuntimeGraphPort
from Runtime.UseCases.AttendIncident.Workflows.AttendIncidentWorkflow import AttendIncidentWorkflow
from Infrastructure.Guardrails.AwsBedrockGuardrail.AwsBedrockGuardrailSetting import BedrockGuardrailSetting
from Infrastructure.Llms.AwsBedrockLlm.AwsBedrockLlmSetting import BedrockLlmSetting
from Infrastructure.Memories.AwsRedisMemory.AwsRedisMemorySetting import RedisMemorySetting
from Infrastructure.Rags.AwsBedrockRag.AwsBedrockRagSetting import BedrockRagSetting
from Infrastructure.Securities.RuntimeSecurity.RuntimeSecuritySetting import SecuritySetting
from Infrastructure.Tools.ApiItopTool.ApiItopToolSetting import ApiItopToolSetting
from Infrastructure.Tools.HttpClientHelper.HttpClientSetting import HttpClientSetting

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

class StartingDI:
    @classmethod
    async def add_services(cls) -> None:
        # -- Infrastructure services
        BedrockLlmSetting.add_services()
        BedrockRagSetting.add_services()
        await RedisMemorySetting.add_services()
        HttpClientSetting.add_services()
        ApiItopToolSetting.add_services()
        BedrockGuardrailSetting.add_services()
        SecuritySetting.add_services()

        # -- Application services
        Services.add_singleton_factory(IRuntimeGraphPort, AttendIncidentWorkflow)
