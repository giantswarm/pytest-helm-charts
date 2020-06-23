import logging

import pytest
from pykube.exceptions import HTTPError

from pytest_helm_charts.apps.app_catalog import AppCatalogFactoryFunc

logger = logging.getLogger(__name__)


def test_app_catalog_add_remove(app_catalog_factory: AppCatalogFactoryFunc):
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
