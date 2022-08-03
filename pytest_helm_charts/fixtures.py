"""This module defines fixtures for testing Helm Charts."""
import logging
import os
import sys
from typing import Iterable, Dict, Mapping

import pytest
from _pytest.config import Config

from pytest_helm_charts.clusters import ExistingCluster, Cluster

logger = logging.getLogger(__name__)

ENV_VAR_CHART_PATH = "ATS_CHART_PATH"
ENV_VAR_CHART_VERSION = "ATS_CHART_VERSION"
ENV_VAR_CLUSTER_TYPE = "ATS_CLUSTER_TYPE"
ENV_VAR_CLUSTER_VERSION = "ATS_CLUSTER_VERSION"
ENV_VAR_APP_CONFIG_PATH = "ATS_APP_CONFIG_FILE_PATH"
ENV_VAR_KUBE_CONFIG = "KUBECONFIG"
ENV_VAR_ATS_EXTRA_PREFIX = "ATS_EXTRA_"
CMD_VAR_TEST_EXTRA_INFO = "test_extra_info"


def get_cmd_line_option_name_from_env_var(env_var_name: str) -> str:
    cmd_name = env_var_name.lower()
    if cmd_name.startswith("ats_"):
        cmd_name = cmd_name[4:]
    return cmd_name


def _load_mandatory_config_option(pytestconfig: Config, env_var_name: str) -> str:
    cmd_name = get_cmd_line_option_name_from_env_var(env_var_name)
    if pytestconfig.getoption(cmd_name):
        return pytestconfig.getoption(cmd_name)
    if env_var_name in os.environ and len(os.environ[env_var_name]) > 0:
        return os.environ[env_var_name]
    raise Exception(
        f"Environment variable '{env_var_name}' (or relevant cmd line option, see help '-h') needed "
        "by a fixture, but not set."
    )


def _load_optional_config_option(pytestconfig: Config, env_var_name: str) -> str:
    cmd_name = get_cmd_line_option_name_from_env_var(env_var_name)
    if pytestconfig.getoption(cmd_name):
        return pytestconfig.getoption(cmd_name)
    return os.environ[env_var_name] if env_var_name in os.environ else ""


def _parse_cmd_opt_extra_info(info: str) -> Dict[str, str]:
    pairs = list(filter(None, info.split(",")))
    res_dict: Dict[str, str] = {}
    for pair in pairs:
        k, v = list(filter(None, pair.split("=")))
        res_dict[k.lower()] = v
    return res_dict


def _filter_extra_info_from_mapping(extra: Mapping[str, str]) -> Dict[str, str]:
    return {
        k[len(ENV_VAR_ATS_EXTRA_PREFIX) :].lower(): v
        for k, v in extra.items()
        if k.startswith(ENV_VAR_ATS_EXTRA_PREFIX)
    }


@pytest.fixture(scope="module")
def chart_path(pytestconfig: Config) -> str:
    """Return a path to the chart under test (from command line argument)."""
    return _load_optional_config_option(pytestconfig, ENV_VAR_CHART_PATH)


@pytest.fixture(scope="module")
def chart_version(pytestconfig: Config) -> str:
    """Return a value that needs to be used as chart version override (from command line argument)."""
    return _load_optional_config_option(pytestconfig, ENV_VAR_CHART_VERSION)


@pytest.fixture(scope="module")
def cluster_type(pytestconfig: Config) -> str:
    """Return a type of cluster used for testing (from command line argument)."""
    return _load_optional_config_option(pytestconfig, ENV_VAR_CLUSTER_TYPE)


@pytest.fixture(scope="module")
def cluster_version(pytestconfig: Config) -> str:
    """Return a type of cluster used for testing (from command line argument)."""
    return _load_optional_config_option(pytestconfig, ENV_VAR_CLUSTER_VERSION)


@pytest.fixture(scope="module")
def values_file_path(pytestconfig: Config) -> str:
    """Return a path to the yaml file that needs to be used to configure chart under test
    (from command line argument).
    """
    return _load_optional_config_option(pytestconfig, ENV_VAR_APP_CONFIG_PATH)


@pytest.fixture(scope="module")
def kube_config(pytestconfig: Config) -> str:
    """Return a path to the kube.config file that points to a running cluster with app
    catalog platform tools already installed."""
    return _load_mandatory_config_option(pytestconfig, ENV_VAR_KUBE_CONFIG)


@pytest.fixture(scope="module")
def test_extra_info(pytestconfig: Config) -> Dict[str, str]:
    """Return an optional dict of variable names and values passed to the test using either
    the `--extra-test-info` cmd line option or env vars prefixed with 'ATS_EXTRA_'."""
    from_env = _filter_extra_info_from_mapping(os.environ)
    if pytestconfig.getoption(CMD_VAR_TEST_EXTRA_INFO):
        from_cmd = _parse_cmd_opt_extra_info(pytestconfig.getoption(CMD_VAR_TEST_EXTRA_INFO))
        from_env.update(from_cmd)
    return from_env


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
