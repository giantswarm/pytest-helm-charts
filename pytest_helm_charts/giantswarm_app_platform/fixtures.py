from typing import List, Iterable

import pytest

from .app import ConfiguredApp, AppFactoryFunc, app_factory_func
from .app_catalog import AppCatalogFactoryFunc, AppCatalogCR, app_catalog_factory_func
from .custom_resources import AppCR
from ..clusters import Cluster


@pytest.fixture(scope="module")
def app_catalog_factory(kube_cluster: Cluster) -> Iterable[AppCatalogFactoryFunc]:
    """Return a factory object, that can be used to configure new AppCatalog CRs
    for the 'app-operator' running in the cluster"""
    created_catalogs: List[AppCatalogCR] = []

    yield app_catalog_factory_func(kube_cluster.kube_client, created_catalogs)

    for catalog in created_catalogs:
        catalog.delete()
        # TODO: wait until finalizer is gone and object is deleted


@pytest.fixture(scope="module")
def app_factory(kube_cluster: Cluster, app_catalog_factory: AppCatalogFactoryFunc) -> Iterable[AppFactoryFunc]:
    """Returns a factory function which can be used to install an app using App CR"""

    created_apps: List[ConfiguredApp] = []

    yield app_factory_func(kube_cluster.kube_client, app_catalog_factory, created_apps)

    for created in created_apps:
        created.app.delete()
        if created.app_cm:
            created.app_cm.delete()
        # TODO: wait until finalizer is gone


@pytest.fixture(scope="module")
def kube_cluster_with_app_platform(
    kube_cluster: Cluster, app_catalog_factory: AppCatalogFactoryFunc
) -> Iterable[Cluster]:
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
