from typing import List, Iterable

import pytest

from pytest_helm_charts.giantswarm_app_platform.app import AppFactoryFunc, app_factory_func
from pytest_helm_charts.giantswarm_app_platform.app_catalog import (
    AppCatalogFactoryFunc,
    AppCatalogCR,
    app_catalog_factory_func,
)
from pytest_helm_charts.giantswarm_app_platform.entities import ConfiguredApp
from pytest_helm_charts.giantswarm_app_platform.utils import delete_app
from pytest_helm_charts.clusters import Cluster
from pytest_helm_charts.fixtures import NamespaceFactoryFunc


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
def app_factory(
    kube_cluster: Cluster, app_catalog_factory: AppCatalogFactoryFunc, namespace_factory: NamespaceFactoryFunc
) -> Iterable[AppFactoryFunc]:
    """Returns a factory function which can be used to install an app using App CR"""

    created_apps: List[ConfiguredApp] = []

    yield app_factory_func(kube_cluster.kube_client, app_catalog_factory, namespace_factory, created_apps)

    for created in created_apps:
        delete_app(created)


# @pytest.fixture(scope="module")
# def my_chart() -> AppCR:
#     """Returns AppCR that can be used to deploy the chart under test using the App Platform
#     tools. The App resource is not yet deployed to the cluster. You need to call create()
#     and delete() to manage its deployment"""
#     # FIXME: implement
#     raise NotImplementedError
