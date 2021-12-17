from typing import List, Iterable

import pytest
from deprecated import deprecated
from pykube import ConfigMap

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
from pytest_helm_charts.clusters import Cluster
from pytest_helm_charts.api.fixtures import NamespaceFactoryFunc
from pytest_helm_charts.utils import object_factory_helper, delete_and_wait_for_objects


@deprecated(version="0.5.3", reason="Please use `catalog_factory` fixture instead.")
@pytest.fixture(scope="module")
def app_catalog_factory(kube_cluster: Cluster) -> Iterable[AppCatalogFactoryFunc]:
    """Return a factory object, that can be used to configure new AppCatalog CRs
    for the 'app-operator' running in the cluster"""
    for o in object_factory_helper(kube_cluster, app_catalog_factory_func, AppCatalogCR):
        yield o


@pytest.fixture(scope="module")
def catalog_factory(kube_cluster: Cluster, namespace_factory: NamespaceFactoryFunc) -> Iterable[CatalogFactoryFunc]:
    """Return a factory object, that can be used to configure new Catalog CRs
    for the 'app-operator' running in the cluster"""
    created_objects: list[CatalogCR] = []

    yield catalog_factory_func(kube_cluster.kube_client, created_objects, namespace_factory)

    delete_and_wait_for_objects(kube_cluster.kube_client, CatalogCR, created_objects)


@pytest.fixture(scope="module")
def app_factory(
    kube_cluster: Cluster, catalog_factory: CatalogFactoryFunc, namespace_factory: NamespaceFactoryFunc
) -> Iterable[AppFactoryFunc]:
    """Returns a factory function which can be used to install an app using App CR"""

    created_apps: List[ConfiguredApp] = []

    yield app_factory_func(kube_cluster.kube_client, catalog_factory, namespace_factory, created_apps)

    apps_to_delete = [a.app for a in created_apps]
    delete_and_wait_for_objects(kube_cluster.kube_client, AppCR, apps_to_delete)
    cms_to_delete = [a.app_cm for a in created_apps if a.app_cm is not None]
    delete_and_wait_for_objects(kube_cluster.kube_client, ConfigMap, cms_to_delete)
