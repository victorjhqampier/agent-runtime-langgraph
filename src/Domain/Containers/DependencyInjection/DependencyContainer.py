from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from threading import RLock
from typing import Any, Callable, Type


class ServiceLifetime(StrEnum):
    SINGLETON = "singleton"
    TRANSIENT = "transient"


@dataclass(slots=True)
class _ServiceRegistration:
    factory: Callable[[], Any]
    lifetime: ServiceLifetime
    instance: Any = None
    initialized: bool = False


class _dependencyContainer:
    """Thread-safe service registry used by the application's composition root."""

    __dependencies: dict[Type[Any], _ServiceRegistration] = {}
    __lock = RLock()

    @classmethod
    def register(cls, service_type: Type[Any], factory: Callable[[], Any], lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT) -> None:
        if not isinstance(service_type, type):
            raise ValueError("Service type is not a valid type")
        if not callable(factory):
            raise ValueError("Service factory must be callable")

        with cls.__lock:
            cls.__dependencies[service_type] = _ServiceRegistration(factory=factory, lifetime=lifetime)

    @classmethod
    def register_instance(cls, service_type: Type[Any], instance: Any) -> None:
        if instance is None:
            raise ValueError("Service instance is NULL")
        cls.register(service_type, lambda: instance, ServiceLifetime.SINGLETON)
        with cls.__lock:
            registration = cls.__dependencies[service_type]
            registration.instance = instance
            registration.initialized = True

    @classmethod
    def resolve(cls, service_type: Type[Any]) -> Any:
        with cls.__lock:
            registration = cls.__dependencies.get(service_type)
            if registration is None:
                return None
            if registration.lifetime == ServiceLifetime.TRANSIENT:
                return registration.factory()
            if not registration.initialized:
                registration.instance = registration.factory()
                registration.initialized = True
            return registration.instance
