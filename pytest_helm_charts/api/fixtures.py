import random
import string
from typing import Protocol, Optional, Iterable, List

import pykube
import pytest

from pytest_helm_charts.clusters import Cluster
from pytest_helm_charts.fixtures import logger
from pytest_helm_charts.utils import ensure_namespace_exists


class NamespaceFactoryFunc(Protocol):
    def __call__(
        self, name: str, extra_metadata: Optional[dict] = None, extra_spec: Optional[dict] = None
    ) -> pykube.Namespace:
        ...


@pytest.fixture(scope="module")
def namespace_factory(kube_cluster: Cluster) -> Iterable[NamespaceFactoryFunc]:
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

        ns = ensure_namespace_exists(kube_cluster.kube_client, name, extra_metadata, extra_spec)
        logger.info(f"Ensured the namespace '{name}'.")
        created_namespaces.append(ns)
        return ns

    yield _namespace_factory

    for created_ns in created_namespaces:
        created_ns.delete()
        logger.info(f"Deleted the namespace '{created_ns.name}'.")


@pytest.fixture(scope="module")
def random_namespace(namespace_factory: NamespaceFactoryFunc) -> pykube.Namespace:
    """Create and return a random kubernetes namespace that will be deleted at the end of test run."""
    name = (
        f"pytest-{''.join(random.choices(string.ascii_lowercase, k=5))}"  # nosec B311 - this is non-cryptographic use
    )
    return namespace_factory(name)
