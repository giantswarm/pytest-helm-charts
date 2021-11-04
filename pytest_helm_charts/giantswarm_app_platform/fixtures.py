from typing import List, Iterable

import pytest
from deprecated import deprecated

from pytest_helm_charts.giantswarm_app_platform.app import AppFactoryFunc, app_factory_func
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
from pytest_helm_charts.giantswarm_app_platform.entities import ConfiguredApp
from pytest_helm_charts.giantswarm_app_platform.utils import delete_app
from pytest_helm_charts.clusters import Cluster
from pytest_helm_charts.fixtures import NamespaceFactoryFunc


@deprecated(version="0.5.3", reason="Please use `catalog_factory` fixture instead.")
@pytest.fixture(scope="module")
def app_catalog_factory(kube_cluster: Cluster) -> Iterable[AppCatalogFactoryFunc]:
    """Return a factory object, that can be used to configure new AppCatalog CRs
    for the 'app-operator' running in the cluster"""
    created_catalogs: List[AppCatalogCR] = []

    yield app_catalog_factory_func(kube_cluster.kube_client, created_catalogs)

    for catalog in created_catalogs:
        catalog.delete()


@pytest.fixture(scope="module")
def catalog_factory(kube_cluster: Cluster, namespace_factory: NamespaceFactoryFunc) -> Iterable[CatalogFactoryFunc]:
    """Return a factory object, that can be used to configure new Catalog CRs
    for the 'app-operator' running in the cluster"""
    created_catalogs: List[CatalogCR] = []

    yield catalog_factory_func(kube_cluster.kube_client, namespace_factory, created_catalogs)

    for catalog in created_catalogs:
        catalog.delete()


@pytest.fixture(scope="module")
def app_factory(
    kube_cluster: Cluster, catalog_factory: CatalogFactoryFunc, namespace_factory: NamespaceFactoryFunc
) -> Iterable[AppFactoryFunc]:
    """Returns a factory function which can be used to install an app using App CR"""

    created_apps: List[ConfiguredApp] = []

    yield app_factory_func(kube_cluster.kube_client, catalog_factory, namespace_factory, created_apps)

    for created in created_apps:
        delete_app(created)
