"""This module defines fixtures for testing Helm Charts."""
import logging
import random
import string
import sys
from typing import Callable, Iterable, Dict, List

import pykube
import pytest
from _pytest.config import Config

from pytest_helm_charts.clusters import ExistingCluster, Cluster
from pytest_helm_charts.utils import ensure_namespace_exists

logger = logging.getLogger(__name__)


@pytest.fixture(scope="module")
def chart_path(pytestconfig: Config) -> str:
    """Return a path to the chart under test (from command line argument)."""
    return pytestconfig.getoption("chart_path")


@pytest.fixture(scope="module")
def chart_version(pytestconfig: Config) -> str:
    """Return a value that needs to be used as chart version override (from command line argument)."""
    return pytestconfig.getoption("chart_version")


def _parse_extra_info(info: str) -> Dict[str, str]:
    pairs = list(filter(None, info.split(",")))
    res_dict: Dict[str, str] = {}
    for pair in pairs:
        k, v = list(filter(None, pair.split("=")))
        res_dict[k] = v
    return res_dict


@pytest.fixture(scope="module")
def chart_extra_info(pytestconfig: Config) -> Dict[str, str]:
    """Return an optional dict of keywords and values passed to the test using '--chart-extra-info' config option."""
    arg = pytestconfig.getoption("chart_extra_info")
    return _parse_extra_info(arg)


@pytest.fixture(scope="module")
def values_file_path(pytestconfig: Config) -> str:
    """Return a path to the yaml file that needs to be used to configure chart under test
    (from command line argument).
    """
    return pytestconfig.getoption("values_file")


@pytest.fixture(scope="module")
def kube_config(pytestconfig: Config) -> str:
    """Return a path to the kube.config file that points to a running cluster with app
    catalog platform tools already installed. Used only if --cluster-type=existing (from command line argument)."""
    return pytestconfig.getoption("kube_config")


@pytest.fixture(scope="module")
def cluster_type(pytestconfig: Config) -> str:
    """Return a type of cluster used for testing (from command line argument)."""
    return pytestconfig.getoption("cluster_type")


ConfigFactoryFunction = Callable[[], Cluster]


@pytest.fixture(scope="module")
def _existing_cluster_factory(kube_config: str) -> ConfigFactoryFunction:
    def _fun() -> Cluster:
        return ExistingCluster(kube_config)

    return _fun


@pytest.fixture(scope="module")
def kube_cluster(
    _existing_cluster_factory: ConfigFactoryFunction,
) -> Iterable[Cluster]:
    """Return a ready Cluster object, which can already be used in test to connect
    to the cluster. Specific implementation used to provide the cluster depends
    on the '--cluster-type' command line option."""
    cluster: Cluster
    cluster = _existing_cluster_factory()

    cluster.create()
    logger.info("Cluster configured")
    yield cluster

    # noinspection PyBroadException
    try:
        cluster.destroy()
        logger.info("Cluster released")
    except Exception:
        exc = sys.exc_info()
        logger.error(f"Error of type {exc[0]} when releasing cluster. Value: {exc[1]}\nStacktrace:\n{exc[2]}")


NamespaceFactoryFunc = Callable[[str], pykube.Namespace]


@pytest.fixture(scope="module")
def namespace_factory(kube_cluster: Cluster) -> Iterable[NamespaceFactoryFunc]:
    """Return a new namespace that is deleted once the fixture is disposed."""
    created_namespaces: List[pykube.Namespace] = []

    def _namespace_factory(name: str) -> pykube.Namespace:
        for namespace in created_namespaces:
            if namespace.metadata["name"] == name:
                return namespace

        ns = ensure_namespace_exists(kube_cluster.kube_client, name)
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
    name = f"pytest-{''.join(random.choices(string.ascii_lowercase, k=5))}"
    return namespace_factory(name)
