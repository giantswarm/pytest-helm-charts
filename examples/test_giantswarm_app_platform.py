import pykube

from pytest_helm_charts.apps.app_catalog import AppCatalogFactoryFunc
from pytest_helm_charts.fixtures import Cluster
import logging

logger = logging.getLogger(__name__)


def test_app_catalog_add_remove(kube_cluster: Cluster, app_catalog_factory: AppCatalogFactoryFunc):
    catalog_name = "test-dynamic"
    catalog_url = "https://test-dynamic.com/"
    catalog = app_catalog_factory(catalog_name, catalog_url)
    assert catalog.metadata["name"] == catalog_name
