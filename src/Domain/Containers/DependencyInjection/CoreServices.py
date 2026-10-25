from typing import Any, Callable, Type, TypeVar

from Domain.Containers.DependencyInjection.DependencyContainer import ServiceLifetime
from Domain.Containers.DependencyInjection.DependencyContainer import _dependencyContainer as DependencyContainer

# ********************************************************************************************************
# * Copyright © 2025 Arify Labs - All rights reserved.
# *
# * Info                  : Core Services for SaaS.
# *
# * By                    : Victor Jhampier Caxi Maquera
# * Email/Mobile/Phone    : victorjhampier@gmail.com | 968991714
# *
# * Creation date         : 24/05/2025
# * ++++++++++++++++++++++++++++++++++++++
# * version             | Descripcion
# * 1.1                 | added singleton and transient factory methods, add_singleton_instance is now singleton trustly registered
# **********************************************************************************************************

T = TypeVar("T")


class CoreServices:
    @staticmethod
    def add_singleton_dependency(interface: Type, implementation: Type) -> None:
        if interface is None or implementation is None:
            raise ValueError("Interface or implementation is NULL")

        if not isinstance(interface, type) or not isinstance(implementation, type):
            raise ValueError("Interface or implementation is not a valid type")

        if not issubclass(implementation, interface):
            raise ValueError(f"{implementation.__name__} must implement {interface.__name__}")

        DependencyContainer.register(interface, implementation, ServiceLifetime.SINGLETON)

    @staticmethod
    def add_transient_dependency(interface: Type, implementation: Type) -> None:
        if interface is None or implementation is None:
            raise ValueError("Interface or implementation is NULL")
        if not isinstance(interface, type) or not isinstance(implementation, type):
            raise ValueError("Interface or implementation is not a valid type")
        if not issubclass(implementation, interface):
            raise ValueError(f"{implementation.__name__} must implement {interface.__name__}")

        DependencyContainer.register(interface, implementation, ServiceLifetime.TRANSIENT)

    @staticmethod
    def add_singleton_factory(interface: Type[T], factory: Callable[[], T]) -> None:
        if interface is None or factory is None:
            raise ValueError("Interface or factory is NULL")
        if not isinstance(interface, type) or not callable(factory):
            raise ValueError("Interface or factory is not valid")

        DependencyContainer.register(interface, factory, ServiceLifetime.SINGLETON)

    @staticmethod
    def add_transient_factory(interface: Type[T], factory: Callable[[], T]) -> None:
        if interface is None or factory is None:
            raise ValueError("Interface or factory is NULL")
        if not isinstance(interface, type) or not callable(factory):
            raise ValueError("Interface or factory is not valid")

        DependencyContainer.register(interface, factory, ServiceLifetime.TRANSIENT)

    @staticmethod
    def get_dependency(interface: Type[T]) -> T:
        if interface is None:
            raise ValueError("Interface is NULL")

        if not isinstance(interface, type):
            raise ValueError("Interface is not a valid type")

        dependency = DependencyContainer.resolve(interface)
        if dependency is not None:
            return dependency
        raise Exception(f"No se encontró implementación para la interfaz {interface}")

    @staticmethod
    def add_singleton_instance(instance: Any) -> None:
        if instance is None:
            raise ValueError("Instance is NULL")

        class_type: type = type(instance)
        if not isinstance(class_type, type):
            raise ValueError("Class type is not a valid type")

        DependencyContainer.register_instance(class_type, instance)

    @staticmethod
    def get_instance(class_type: Type[T]) -> T:
        if class_type is None:
            raise ValueError("Class type is NULL")

        if not isinstance(class_type, type):
            raise ValueError("Class type is not a valid type")

        instance = DependencyContainer.resolve(class_type)
        if instance is not None:
            return instance
        raise Exception(f"No implementation found for interface {class_type}")
