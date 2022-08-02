"""This module defines fixtures for testing Helm Charts."""
import logging
import os
import sys
from typing import Iterable, Dict, Mapping

import pytest

from pytest_helm_charts.clusters import ExistingCluster, Cluster

logger = logging.getLogger(__name__)

CHART_PATH = "ATS_CHART_PATH"
CHART_VERSION = "ATS_CHART_VERSION"
CLUSTER_TYPE = "ATS_CLUSTER_TYPE"
CLUSTER_VERSION = "ATS_CLUSTER_VERSION"
TEST_TYPE = "ATS_TEST_TYPE"
TEST_DIR = "ATS_TEST_DIR"
APP_CONFIG_PATH = "ATS_APP_CONFIG_FILE_PATH"
KUBE_CONFIG = "KUBECONFIG"
ATS_EXTRA_PREFIX = "ATS_EXTRA_"


def _load_mandatory_from_environ(var_name: str) -> str:
    if var_name in os.environ and len(os.environ[var_name]) > 0:
        return os.environ[var_name]
    raise Exception(f"Environment variable '{var_name}' needed by a fixture, but not set.")


def _load_optional_from_environ(var_name: str) -> str:
    return os.environ[var_name] if var_name in os.environ else ""


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
def test_type() -> str:
    """Return a type of the test requested in the current run."""
    return _load_optional_from_environ(TEST_TYPE)


@pytest.fixture(scope="module")
def test_dir() -> str:
    """Return a type of the test requested in the current run."""
    return _load_optional_from_environ(TEST_TYPE)


@pytest.fixture(scope="module")
def values_file_path() -> str:
    """Return a path to the yaml file that needs to be used to configure chart under test
    (from command line argument).
    """
    return _load_optional_from_environ(APP_CONFIG_PATH)


@pytest.fixture(scope="module")
def kube_config() -> str:
    """Return a path to the kube.config file that points to a running cluster with app
    catalog platform tools already installed."""
    return _load_mandatory_from_environ(KUBE_CONFIG)


def _parse_extra_info(info: str) -> Dict[str, str]:
    pairs = list(filter(None, info.split(",")))
    res_dict: Dict[str, str] = {}
    for pair in pairs:
        k, v = list(filter(None, pair.split("=")))
        res_dict[k] = v
    return res_dict


def _filter_extra_info_from_mapping(extra: Mapping[str, str]) -> Dict[str, str]:
    return {k[len(ATS_EXTRA_PREFIX):].lower(): v for k, v in extra.items() if k.startswith(ATS_EXTRA_PREFIX)}


@pytest.fixture(scope="module")
def test_extra_info() -> Dict[str, str]:
    """Return an optional dict of variable names and values passed to the test using env vars prefixed with
     'ATS_EXTRA_' env var."""
    return _filter_extra_info_from_mapping(os.environ)


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
