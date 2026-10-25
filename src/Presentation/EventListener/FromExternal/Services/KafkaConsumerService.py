from __future__ import annotations
import asyncio
import json
import uuid
from typing import Any, Awaitable, Callable, List, Union, TypeVar, Generic, cast
from Presentation.EventListener.FromExternal.Collections.ExampleTopicCollection import ExampleTopicCollection
from Presentation.EventListener.FromExternal.Services.KafkaConsumerBuilder import KafkaConsumerBuilder
from Presentation.EventListener.FromExternal.Services.KafkaConsumerLogger import KafkaConsumerLogger
from aiokafka import AIOKafkaConsumer, ConsumerRecord

T = TypeVar("T")


class KafkaConsumerService(Generic[T]):
    def __init__(self) -> None:
        self.__topic: Union[str, List[str]] | None = None
        self.__group_id: str | None = None
        self.__bootstrap: str | None = None
        self.__handler: Callable[[T], Awaitable[Any]] | None = None
        self.__value_deserializer: Callable[[bytes], Any] | None = None
        self.__client_id: str | None = None
        self.__stop_event = asyncio.Event()
        self.__task: asyncio.Task | None = None
        self.__consumer: AIOKafkaConsumer | None = None
        self._logger = KafkaConsumerLogger.set_logger().getChild(self.__class__.__name__)

    def with_topic(self, topic: Union[str, List[str]]) -> "KafkaConsumerService[T]":
        self.__topic = topic
        return self

    def with_bootstrap_servers(self, bootstrap: str) -> "KafkaConsumerService[T]":
        self.__bootstrap = bootstrap
        return self

    def with_group_id(self, group_id: str) -> "KafkaConsumerService[T]":
        self.__group_id = group_id
        return self

    def with_handler(self, handler: Callable[[T], Awaitable[Any]]) -> "KafkaConsumerService[T]":
        self.__handler = handler
        return self

    def with_value_deserializer(self, deserializer: Callable[[bytes], Any]) -> "KafkaConsumerService[T]":
        self.__value_deserializer = deserializer
        return self

    def with_client_id(self, client_id: str) -> "KafkaConsumerService[T]":
        self.__client_id = client_id
        return self

    def _validate(self) -> None:
        if not self.__topic:
            raise ValueError("Topic is required")
        if not self.__group_id:
            raise ValueError("Group ID is required")
        if not self.__bootstrap:
            raise ValueError("Bootstrap servers are required")
        if not self.__handler:
            raise ValueError("Handler is required")

    async def start(self) -> None:
        self._validate()

        if self.__task:
            return

        self.__consumer = KafkaConsumerBuilder(
            bootstrap_servers=self.__bootstrap,
            value_deserializer=self.__value_deserializer or (lambda v: json.loads(v.decode())),
        ).build(
            topic=self.__topic,
            group_id=self.__group_id,
            client_id=self.__client_id or f"arifylabs-{uuid.uuid4()}",
        )

        await self.__consumer.start()
        self.__task = asyncio.create_task(self._loop())
        self._logger.info("KafkaWorker [%s] started", self.__consumer._client)

    async def stop(self) -> None:
        self.__stop_event.set()
        if self.__task:
            await self.__task
        if self.__consumer:
            await self.__consumer.stop()
            self._logger.info("KafkaWorker [%s] stopped", self.__consumer._client)

    async def _loop(self) -> None:
        while not self.__stop_event.is_set():
            try:
                consumer = self.__consumer
                if consumer is None:
                    raise RuntimeError("Kafka consumer is not started")

                batches = await consumer.getmany(
                    timeout_ms=1000,
                    max_records=100,
                )
                for tp, records in batches.items():
                    for record in records:
                        await self._dispatch(record)
                    await consumer.commit()
            except Exception as exc:
                self._logger.error("Error en loop Kafka: %s", exc)

    async def _dispatch(self, record: ConsumerRecord) -> None:
        try:
            handler = self.__handler
            if handler is None:
                raise RuntimeError("Kafka handler is not configured")

            message = ExampleTopicCollection.model_validate(record.value)
            await handler(cast(T, message))
        except Exception as ex:
            self._logger.error("Fallo procesando offset=%s partition=%s detail=[%s]", record.offset, record.partition, str(ex))
