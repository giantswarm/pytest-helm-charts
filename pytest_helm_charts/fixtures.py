"""This module defines fixtures for testing Helm Charts."""
import logging
import os.path
import sys
from pathlib import Path
from typing import Callable, List, Iterable

import pytest
from _pytest.config import Config
from _pytest.config.argparsing import Parser
from pykube import HTTPClient

from .apps.app_catalog import AppCR, AppCatalogFactoryFunc
from .apps.deployment import AppFactoryFunc, AppState, app_factory_func
from .clusters import ExistingCluster, Cluster

logger = logging.getLogger(__name__)


def pytest_addoption(parser: Parser) -> None:
    group = parser.getgroup("kube-provider")
    group.addoption(
        "--cluster-type",
        action="store",
        default="existing",
        help="Select cluster type. Supported values: 'kind', 'existing'."
    )
    group.addoption(
        "--kube-config",
        action="store",
        default=os.path.join(str(Path.home()), ".kube", "config"),
        help="The path to 'kube.config' file. Used when '--cluster-type existing' is used as well."
    )
    group.addoption(
        "--values-file",
        action="store",
        help="Path to the values file used for testing the chart."
    )
    group.addoption(
        "--chart-path",
        action="store",
        help="The path to a helm chart under test."
    )
    group.addoption(
        "--chart-version",
        action="store",
        help="Override chart version for the chart under test."
    )


@pytest.fixture(scope="module")
def chart_path(pytestconfig: Config) -> str:
    """Return a path to the chart under test (from command line argument)."""
    return pytestconfig.getoption("chart_path")


@pytest.fixture(scope="module")
def chart_version(pytestconfig: Config) -> str:
    """Return a value that needs to be used as chart version override (from command line argument)."""
    return pytestconfig.getoption("chart_version")


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
    """Return a type of cluster to provide to the test environment. Currently supported values are:
    "existing", "kind", "giantswarm"."""
    return pytestconfig.getoption("cluster_type")


ConfigFactoryFunction = Callable[[], Cluster]


@pytest.fixture(scope="module")
def _existing_cluster_factory(kube_config: str) -> ConfigFactoryFunction:
    def _fun() -> Cluster:
        return ExistingCluster(kube_config)

    return _fun


@pytest.fixture(scope="module")
def _kind_cluster_factory() -> ConfigFactoryFunction:
    def _fun() -> Cluster:
        # FIXME: implement
        raise NotImplementedError

    return _fun


@pytest.fixture(scope="module")
def _giantswarm_cluster_factory() -> ConfigFactoryFunction:
    def _fun() -> Cluster:
        # FIXME: implement
        raise NotImplementedError

    return _fun


@pytest.fixture(scope="module")
def kube_cluster(cluster_type: str,
                 _existing_cluster_factory: ConfigFactoryFunction,
                 _kind_cluster_factory: ConfigFactoryFunction,
                 _giantswarm_cluster_factory: ConfigFactoryFunction) -> Iterable[Cluster]:
    """Return a ready Cluster object, which can already be used in test to connect
    to the cluster. Specific implementation used to provide the cluster depends
    on the '--cluster-type' command line option."""
    cluster: Cluster
    created_clusters: List[Cluster] = []
    if cluster_type == "existing":
        cluster = _existing_cluster_factory()
    elif cluster_type == "kind":
        cluster = _kind_cluster_factory()
    elif cluster_type == "giantswarm":
        cluster = _giantswarm_cluster_factory()
    else:
        raise ValueError("Unsupported cluster type '{}'.".format(cluster_type))

    logger.info("Creating new cluster of type '{}'.".format(cluster_type))
    cluster.create()
    logger.info("Cluster created")
    created_clusters.append(cluster)
    yield cluster

    for c in created_clusters:
        try:
            logger.info("Destroying cluster")
            c.destroy()
            logger.info("Cluster destroyed")
        except:
            exc = sys.exc_info()
            logger.error("Error of type {} when destroying cluster. Value: {}\nStacktrace:\n{}".format(
                exc[0], exc[1], exc[2]
            ))


@pytest.fixture(scope="session")
def app_factory(kube_client: HTTPClient,
                app_catalog_factory: AppCatalogFactoryFunc) -> Iterable[AppFactoryFunc]:
    """Returns a factory function which can be used to install an app using App CR"""

    created_apps: List[AppState] = []

    yield app_factory_func(kube_client, app_catalog_factory, created_apps)

    for created in created_apps:
        created.app.delete()
        if created.app_cm:
            created.app_cm.delete()
        # TODO: wait until finalizer is gone


@pytest.fixture(scope="module")
def kube_cluster_with_app_catalog(kube_cluster: Cluster,
                                  app_catalog_factory: AppCatalogFactoryFunc) -> Iterable[Cluster]:
    """Get a ready cluster based on '--cluster-type' command line argument. Additionally,
    preconfigure the cluster with Giant Swarm's Application Platform, including:
    - app-operator
    - chart-operator
    - chartmuseum (for storing custom build time charts)
    - AppCatalog Custom Resource configured for the chartmuseum."""
    # FIXME: implement
    # TODO:
    # - deploy app-operator
    # - deploy chartmuseum
    # - create new AppCatalog CR with app_catalog_factory to register chartmuseum as catalog
    raise NotImplementedError
    # yield kube_cluster
    # TODO:
    # - destroy app-operator
    # - destroy chartmuseum


@pytest.fixture(scope="module")
def my_chart() -> AppCR:
    """Returns AppCR that can be used to deploy the chart under test using the App Platform
    tools. The App resource is not yet deployed to the cluster. You need to call create()
    and delete() to manage its deployment"""
    # FIXME: implement
    raise NotImplementedError


@pytest.fixture(scope="module")
def app_factory(kube_client: HTTPClient,
                app_catalog_factory: AppCatalogFactoryFunc) -> Iterable[AppFactoryFunc]:
    """Returns a factory function which can be used to install an app using App CR"""

    created_apps: List[AppState] = []

    yield app_factory_func(kube_client, app_catalog_factory, created_apps)
    for created in created_apps:
        created.app.delete()
        if created.app_cm:
            created.app_cm.delete()
        # TODO: wait until finalizer is gone
