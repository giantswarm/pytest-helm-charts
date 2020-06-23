import logging

import pytest
from pykube.exceptions import HTTPError
from pytest_helm_charts.giantswarm_app_platform.app import AppFactoryFunc

from pytest_helm_charts.giantswarm_app_platform.app_catalog import AppCatalogFactoryFunc

logger = logging.getLogger(__name__)


def test_app_catalog_factory_fixture(app_catalog_factory: AppCatalogFactoryFunc):
    """This example shows how to use [app_catalog_factory](pytest_helm_charts.fixtures.app_app_catalog_factory)
    fixture to create a new AppCatalog CR in the Kubernetes API. You have to define an app catalog before you
    can install and use applications coming from that catalog.
    """
    catalog_name = "test-dynamic"
    catalog_url = "https://test-dynamic.com/"
    catalog = app_catalog_factory(catalog_name, catalog_url)
    assert catalog.metadata["name"] == catalog_name
    assert catalog.obj["spec"]["title"] == catalog_name
    assert catalog.obj["spec"]["storage"]["type"] == "helm"
    assert catalog.obj["spec"]["storage"]["URL"] == catalog_url


@pytest.mark.xfail(raises=HTTPError)
def test_app_catalog_bad_name(app_catalog_factory: AppCatalogFactoryFunc):
    catalog_name = "test_dynamic"
    catalog_url = "https://test-dynamic.com/"
    catalog = app_catalog_factory(catalog_name, catalog_url)
    assert catalog.metadata["name"] == catalog_name


def test_app_factory_fixture(app_factory: AppFactoryFunc):
    """Instead of using the [app_factory](pytest_helm_charts.fixtures.app_factory) fixture
    directly to create a new app here, we test the specific case of using it to create
    [stormforger_load_app_factory](pytest_helm_charts.fixtures."""
    catalog_name = "test-dynamic"
    catalog_url = "https://test-dynamic.com/"
    catalog = app_catalog_factory(catalog_name, catalog_url)
    assert catalog.metadata["name"] == catalog_name
