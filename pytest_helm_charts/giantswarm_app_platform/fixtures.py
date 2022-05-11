import logging
from typing import List, Iterable

import pytest
from deprecated import deprecated
from pykube import ConfigMap

from pytest_helm_charts.k8s.fixtures import NamespaceFactoryFunc
from pytest_helm_charts.clusters import Cluster
from pytest_helm_charts.giantswarm_app_platform.app import (
    AppFactoryFunc,
    app_factory_func,
    ConfiguredApp,
    AppCR,
)
from pytest_helm_charts.giantswarm_app_platform.app_catalog import (
    AppCatalogFactoryFunc,
    AppCatalogCR,
    app_catalog_factory_func,
)
from pytest_helm_charts.giantswarm_app_platform.catalog import (
    CatalogFactoryFunc,
    CatalogCR,
    catalog_factory_func,
)
from pytest_helm_charts.utils import object_factory_helper, delete_and_wait_for_objects

logger = logging.getLogger(__name__)


@deprecated(version="0.5.3", reason="Please use `catalog_factory` fixture instead.")
@pytest.fixture(scope="module")
def app_catalog_factory(kube_cluster: Cluster) -> Iterable[AppCatalogFactoryFunc]:
    """
    [Obsolete]
    Please use
    [_catalog_factory](pytest_helm_charts.giantswarm_app_platform.catalog._catalog_factory) instead.

    Return a factory object, that can be used to configure new AppCatalog CRs
    for the 'app-operator' running in the cluster. Fixture's scope is 'module'.
    """
    yield from object_factory_helper(kube_cluster, app_catalog_factory_func, AppCatalogCR)


@pytest.fixture(scope="function")
def catalog_factory_function_scope(
    kube_cluster: Cluster, namespace_factory: NamespaceFactoryFunc
) -> Iterable[CatalogFactoryFunc]:
    """Return a factory object, that can be used to configure new Catalog CRs
    for the 'app-operator' running in the cluster. Fixture's scope is 'function'."""
    yield from _catalog_factory_impl(kube_cluster, namespace_factory)


@pytest.fixture(scope="module")
def catalog_factory(kube_cluster: Cluster, namespace_factory: NamespaceFactoryFunc) -> Iterable[CatalogFactoryFunc]:
    """Return a factory object, that can be used to configure new Catalog CRs
    for the 'app-operator' running in the cluster. Fixture's scope is 'module'."""
    yield from _catalog_factory_impl(kube_cluster, namespace_factory)


def _catalog_factory_impl(
    kube_cluster: Cluster, namespace_factory: NamespaceFactoryFunc
) -> Iterable[CatalogFactoryFunc]:
    created_objects: List[CatalogCR] = []

    yield catalog_factory_func(kube_cluster.kube_client, created_objects, namespace_factory)

    delete_and_wait_for_objects(kube_cluster.kube_client, CatalogCR, created_objects)


@pytest.fixture(scope="module")
def app_factory(
    kube_cluster: Cluster, catalog_factory: CatalogFactoryFunc, namespace_factory: NamespaceFactoryFunc
) -> Iterable[AppFactoryFunc]:
    """Returns a factory function which can be used to install an app using App CR. Fixture's scope is 'module'."""
    yield from _app_factory_impl(kube_cluster, catalog_factory, namespace_factory)


@pytest.fixture(scope="function")
def app_factory_function_scope(
    kube_cluster: Cluster, catalog_factory: CatalogFactoryFunc, namespace_factory: NamespaceFactoryFunc
) -> Iterable[AppFactoryFunc]:
    """Returns a factory function which can be used to install an app using App CR. Fixture's scope is 'module'."""
    yield from _app_factory_impl(kube_cluster, catalog_factory, namespace_factory)


def _app_factory_impl(
    kube_cluster: Cluster, catalog_factory: CatalogFactoryFunc, namespace_factory: NamespaceFactoryFunc
) -> Iterable[AppFactoryFunc]:
    """Returns a factory function which can be used to install an app using App CR."""

    created_apps: List[ConfiguredApp] = []

    yield app_factory_func(kube_cluster.kube_client, catalog_factory, namespace_factory, created_apps)

    apps_to_delete = [a.app for a in created_apps]
    delete_and_wait_for_objects(kube_cluster.kube_client, AppCR, apps_to_delete)
    cms_to_delete = [a.app_cm for a in created_apps if a.app_cm is not None]
    delete_and_wait_for_objects(kube_cluster.kube_client, ConfigMap, cms_to_delete)
