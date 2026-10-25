import logging

from Infrastructure.InfrastructureLogger import InfrastructureLogger


class KafkaConsumerLogger:
    @staticmethod
    def set_logger() -> logging.Logger:
        return InfrastructureLogger.set_logger().getChild("KafkaConsumerLogger")
