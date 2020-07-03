import logging

import pytest
from pykube.exceptions import HTTPError

from pytest_helm_charts.giantswarm_app_platform.app_catalog import AppCatalogFactoryFunc
from pytest_helm_charts.giantswarm_app_platform.apps.http_testing import StormforgerLoadAppFactoryFunc

logger = logging.getLogger(__name__)


def test_app_catalog_factory_fixture(app_catalog_factory: AppCatalogFactoryFunc):
    """This example shows how to use
    [app_catalog_factory](pytest_helm_charts.giantswarm_app_platform.fixtures.app_app_catalog_factory)
    fixture to create a new AppCatalog CR in the Kubernetes API. You have to define an app catalog before you
    can install and use applications coming from that catalog.
    """
    catalog_name = "test-dynamic"
    catalog_url = "https://test-dynamic.com"
    catalog = app_catalog_factory(catalog_name, catalog_url)
    assert catalog.metadata["name"] == catalog_name
    assert catalog.obj["spec"]["title"] == catalog_name
    assert catalog.obj["spec"]["storage"]["type"] == "helm"
    assert catalog.obj["spec"]["storage"]["URL"] == catalog_url


@pytest.mark.xfail(raises=HTTPError)
def test_app_catalog_bad_name(app_catalog_factory: AppCatalogFactoryFunc):
    """This example is the same as [test_test_app_catalog_factory_fixture](test_app_catalog_factory_fixture)
    but raises an Exception, as 'test_dynamic' is not a correct name in Kubernetes API. Be careful
    and check for Kubernetes API restrictions as well. In this case, a DNS-compatible name is required.
    """
    catalog_name = "test_dynamic"
    catalog_url = "https://test-dynamic.com/"
    catalog = app_catalog_factory(catalog_name, catalog_url)
    assert catalog.metadata["name"] == catalog_name


def test_app_factory_fixture(stormforger_load_app_factory: StormforgerLoadAppFactoryFunc):
    """Instead of using the [app_factory](pytest_helm_charts.giantswarm_app_platform.fixtures.app_factory) fixture
    directly to create a new app here, we test the specific case of using it to create
    [stormforger_load_app_factory](pytest_helm_charts.giantswarm_app_platforms.apps.http_testing.stormforger_load_app_factory),
    which works exactly by using the [app_factory](pytest_helm_charts.giantswarm_app_platform.fixtures.app_factory)
    fixture.
    """
    configured_app = stormforger_load_app_factory(1, "loadtest.app", None)
    assert configured_app.app.name == "loadtest-app"
    assert configured_app.app.metadata["name"] == "loadtest-app"
    assert "app-operator.giantswarm.io/version" in configured_app.app.metadata["labels"]
    assert configured_app.app.obj["kind"] == "App"
