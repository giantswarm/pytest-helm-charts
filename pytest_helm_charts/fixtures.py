"""This module defines fixtures for testing Helm Charts."""
import logging
import sys
from typing import Iterable, Dict, Protocol

import pytest
from _pytest.config import Config
from pytest_helm_charts.clusters import ExistingCluster, Cluster

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
def test_extra_info(pytestconfig: Config) -> Dict[str, str]:
    """Return an optional dict of keywords and values passed to the test using '--test-extra-info' config option."""
    arg = pytestconfig.getoption("test_extra_info")
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


class ConfigFactoryFunction(Protocol):
    def __call__(self) -> Cluster:
        pass


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
    logger.debug("Cluster connection configured")
    yield cluster

    # noinspection PyBroadException
    try:
        cluster.destroy()
        logger.debug("Cluster connection released")
    except Exception:
        exc = sys.exc_info()
        logger.error(f"Error of type {exc[0]} when releasing cluster. Value: {exc[1]}\nStacktrace:\n{exc[2]}")
