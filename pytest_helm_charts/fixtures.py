"""This module defines fixtures for testing Helm Charts."""
import logging
import os
import sys
from typing import Iterable, Dict, Protocol

import pytest
from _pytest.config import Config
from pytest_helm_charts.clusters import ExistingCluster, Cluster

logger = logging.getLogger(__name__)

CHART_PATH = "ATS_CHART_PATH"
CHART_VERSION = "ATS_CHART_VERSION"

CLUSTER_TYPE = "ATS_CLUSTER_TYPE"
CLUSTER_VERSION = "ATS_CLUSTER_VERSION"
KUBE_CONFIG = "ATS_KUBE_CONFIG_PATH"
TEST_TYPE = "ATS_TEST_TYPE"
TEST_DIR = "ATS_TEST_DIR"
APP_CONFIG_PATH = "ATS_APP_CONFIG_FILE_PATH"


def _load_mandatory_from_environ(var_name: str) -> str:
    if var_name in os.environ and len(os.environ[var_name]):
        return os.environ[var_name]
    raise Exception(f"Environment variable '{var_name}' needed by a fixture, but not set.")


@pytest.fixture(scope="module")
def chart_path() -> str:
    """Return a path to the chart under test (from command line argument)."""
    return _load_mandatory_from_environ(CHART_PATH)


@pytest.fixture(scope="module")
def chart_version() -> str:
    """Return a value that needs to be used as chart version override (from command line argument)."""
    return _load_mandatory_from_environ(CHART_VERSION)


@pytest.fixture(scope="module")
def cluster_type() -> str:
    """Return a type of cluster used for testing (from command line argument)."""
    return _load_mandatory_from_environ(CLUSTER_TYPE)


@pytest.fixture(scope="module")
def cluster_version() -> str:
    """Return a type of cluster used for testing (from command line argument)."""
    return _load_mandatory_from_environ(CLUSTER_VERSION)


@pytest.fixture(scope="module")
def values_file_path() -> str:
    """Return a path to the yaml file that needs to be used to configure chart under test
    (from command line argument).
    """
    return os.environ[APP_CONFIG_PATH] if APP_CONFIG_PATH in os.environ else ""


@pytest.fixture(scope="module")
def kube_config() -> str:
    """Return a path to the kube.config file that points to a running cluster with app
    catalog platform tools already installed. Used only if --cluster-type=existing (from command line argument)."""
    return _load_mandatory_from_environ(KUBE_CONFIG)




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


class ConfigFactoryFunction(Protocol):
    def __call__(self) -> Cluster:
        pass


@pytest.fixture(scope="module")
def kube_cluster(
    kube_config: str,
) -> Iterable[Cluster]:
    """Return a ready Cluster object, which can already be used in test to connect
    to the cluster. Specific implementation used to provide the cluster depends
    on the '--cluster-type' command line option."""
    cluster = ExistingCluster(kube_config)

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
