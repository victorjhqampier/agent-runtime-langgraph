from __future__ import annotations
import uuid
from typing import Any, Callable, Dict, List, Union
from Presentation.EventListener.FromExternal.Services.KafkaDefaultConfig import KafkaDefaultConfig
from aiokafka import AIOKafkaConsumer


class KafkaConsumerBuilder:
    def __init__(
        self,
        bootstrap_servers: str | None = None,
        *,
        value_deserializer: Callable[[bytes], Any] | None = None,
        **extra_conf: Any,
    ) -> None:
        self.__default_settings = KafkaDefaultConfig()
        self._config: Dict[str, Any] = {
            "bootstrap_servers": bootstrap_servers or self.__default_settings.bootstrap_servers,
            "enable_auto_commit": False,
            "auto_offset_reset": "earliest",
            "value_deserializer": value_deserializer or (lambda v: v.decode()),
        }
        self._config.update(extra_conf)

        if self.__default_settings.ssl_enabled:
            self._config.update(
                security_protocol="SSL",
                ssl_cafile=self.__default_settings.ssl_cafile,
                ssl_certfile=self.__default_settings.ssl_certfile,
                ssl_keyfile=self.__default_settings.ssl_keyfile,
            )

    # Crea el consumidor (sin --start todavía).
    def build(
        self,
        *,
        topic: Union[str, List[str]] | None = None,
        group_id: str | None = None,
        client_id: str | None = None,
    ) -> AIOKafkaConsumer:
        cfg = self._config.copy()
        cfg["group_id"] = group_id or self.__default_settings.group_id
        cfg["client_id"] = client_id or f"arifylabs-{uuid.uuid4()}"
        topics = topic if topic is not None else self.__default_settings.topic
        return AIOKafkaConsumer(topics, **cfg)
