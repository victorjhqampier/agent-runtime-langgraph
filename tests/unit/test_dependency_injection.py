import sys
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from Domain.Containers.DependencyInjection.CoreServices import CoreServices


class SingletonContract:
    pass


class SingletonImplementation(SingletonContract):
    pass


class TransientContract:
    pass


class TransientImplementation(TransientContract):
    pass


class FactoryContract:
    pass


class FactoryImplementation(FactoryContract):
    pass


class DependencyInjectionTests(unittest.TestCase):
    def test_singleton_dependency_returns_the_same_instance(self) -> None:
        CoreServices.add_singleton_dependency(SingletonContract, SingletonImplementation)

        first = CoreServices.get_dependency(SingletonContract)
        second = CoreServices.get_dependency(SingletonContract)

        self.assertIs(first, second)

    def test_transient_dependency_returns_a_new_instance(self) -> None:
        CoreServices.add_transient_dependency(TransientContract, TransientImplementation)

        first = CoreServices.get_dependency(TransientContract)
        second = CoreServices.get_dependency(TransientContract)

        self.assertIsNot(first, second)

    def test_singleton_instance_keeps_its_existing_facade(self) -> None:
        instance = SingletonImplementation()
        CoreServices.add_singleton_instance(instance)

        self.assertIs(instance, CoreServices.get_instance(SingletonImplementation))

    def test_singleton_factory_creates_one_instance_under_concurrent_resolution(self) -> None:
        factory_calls = 0

        def factory() -> FactoryContract:
            nonlocal factory_calls
            factory_calls += 1
            return FactoryImplementation()

        CoreServices.add_singleton_factory(FactoryContract, factory)
        with ThreadPoolExecutor(max_workers=8) as executor:
            instances = list(executor.map(lambda _: CoreServices.get_dependency(FactoryContract), range(32)))

        self.assertEqual(1, factory_calls)
        self.assertTrue(all(instance is instances[0] for instance in instances))
