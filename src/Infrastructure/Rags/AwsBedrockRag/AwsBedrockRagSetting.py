from Domain.Interfaces.Queries.IEvidenceQuery import IEvidenceQuery
from Domain.Containers.DependencyInjection.CoreServices import CoreServices as Services
from Infrastructure.Rags.AwsBedrockRag.BedrockRagSettings import BedrockRagSettings
from Infrastructure.Rags.AwsBedrockRag.Queries.RetrieveBedrockKnowledgeQuery import RetrieveBedrockKnowledgeQuery


class BedrockRagSetting:
    @classmethod
    def add_services(cls) -> None:
        settings = BedrockRagSettings()
        if settings.provider != "AWS_BEDROCK":
            raise ValueError("RUNTIME_RAG_PROVIDER must be AWS_BEDROCK for BedrockRagSetting")
        query = RetrieveBedrockKnowledgeQuery(settings)
        Services.add_singleton_instance(query)
        Services.add_singleton_factory(IEvidenceQuery, lambda: query)
