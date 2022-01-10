import random
import string
from typing import Protocol, Optional, Iterable, List

import pykube
import pytest

from pytest_helm_charts.clusters import Cluster
from pytest_helm_charts.fixtures import logger
from pytest_helm_charts.k8s.namespace import ensure_namespace_exists
from pytest_helm_charts.utils import delete_and_wait_for_objects


class NamespaceFactoryFunc(Protocol):
    def __call__(
        self, name: str, extra_metadata: Optional[dict] = None, extra_spec: Optional[dict] = None
    ) -> pykube.Namespace:
        ...


@pytest.fixture(scope="function")
def namespace_factory_function_scope(kube_cluster: Cluster) -> Iterable[NamespaceFactoryFunc]:
    """Return a new namespace that is deleted once the fixture is disposed. Fixture's scope is 'function'."""
    yield from _namespace_factory_impl(kube_cluster)


@pytest.fixture(scope="module")
def namespace_factory(kube_cluster: Cluster) -> Iterable[NamespaceFactoryFunc]:
    """Return a new namespace that is deleted once the fixture is disposed. Fixture's scope is 'module'."""
    yield from _namespace_factory_impl(kube_cluster)


def _namespace_factory_impl(kube_cluster: Cluster) -> Iterable[NamespaceFactoryFunc]:
    """Return a new namespace that is deleted once the fixture is disposed."""
    created_namespaces: List[pykube.Namespace] = []

    def _namespace_factory(
        name: str,
        extra_metadata: Optional[dict] = None,
        extra_spec: Optional[dict] = None,
    ) -> pykube.Namespace:
        for namespace in created_namespaces:
            if namespace.metadata["name"] == name:
                return namespace

        ns, created = ensure_namespace_exists(kube_cluster.kube_client, name, extra_metadata, extra_spec)
        logger.debug(f"Ensured the namespace '{name}'.")
        if created:
            created_namespaces.append(ns)
        return ns

    yield _namespace_factory

    delete_and_wait_for_objects(kube_cluster.kube_client, pykube.Namespace, created_namespaces)


def _random_ns_name() -> str:
    return f"pytest-{''.join(random.choices(string.ascii_lowercase, k=5))}"  # nosec B311 - non-cryptographic use


@pytest.fixture(scope="function")
def random_namespace_function_scope(namespace_factory: NamespaceFactoryFunc) -> pykube.Namespace:
    """Create and return a random kubernetes namespace that will be deleted at the end of test run.
    Fixture's scope is 'module'."""
    return namespace_factory(_random_ns_name())


@pytest.fixture(scope="module")
def random_namespace(namespace_factory: NamespaceFactoryFunc) -> pykube.Namespace:
    """Create and return a random kubernetes namespace that will be deleted at the end of test run.
    Fixture's scope is 'module'."""
    return namespace_factory(_random_ns_name())
