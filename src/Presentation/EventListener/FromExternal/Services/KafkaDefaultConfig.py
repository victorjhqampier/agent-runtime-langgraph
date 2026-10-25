from pydantic import Field, BaseModel


class KafkaDefaultConfig(BaseModel):
    bootstrap_servers: str = Field("10.4.12.12")
    topic: str = Field("default-topic")
    group_id: str = Field("default-group")

    # TLS/SASL opcional
    ssl_enabled: bool = Field(False)
    ssl_cafile: str | None = Field(None)
    ssl_certfile: str | None = Field(None)
    ssl_keyfile: str | None = Field(None)
