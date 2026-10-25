from Presentation.EventListener.FromExternal.Collections.ExampleTopicCollection import ExampleTopicCollection
import time

from Presentation.EventListener.FromExternal.Services.KafkaConsumerLogger import KafkaConsumerLogger


class ExamExecuteFromKafkaQuery:
    def __init__(self, event: ExampleTopicCollection) -> None:
        self.__event = event
        self._logger = KafkaConsumerLogger.set_logger().getChild(self.__class__.__name__)

    @classmethod
    async def handler(cls, event: ExampleTopicCollection):
        instance = cls(event)
        await instance.handle_vcaxi()
        return instance

    # ------ Método que recibe los eventos de kafka
    async def handle_vcaxi(self) -> None:
        # time.sleep(3)
        self._logger.warning(f"Arify: [handler-1] order {str(self.__event)}")
