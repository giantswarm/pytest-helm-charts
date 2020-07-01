from typing import Optional

from _pytest.pytester import Testdir
from pytest_mock import MockFixture

import pytest_helm_charts.giantswarm_app_platform.app_catalog
import pytest_helm_charts.giantswarm_app_platform.custom_resources
from pytest_helm_charts.clusters import Cluster
from pytest_helm_charts.giantswarm_app_platform.app import AppFactoryFunc
from pytest_helm_charts.giantswarm_app_platform.custom_resources import AppCatalogCR
from pytest_helm_charts.utils import YamlDict
from tests.helper import run_pytest


def test_app_catalog_working(testdir: Testdir, mocker: MockFixture):
    testdir.copy_example("examples/test_giantswarm_app_platform.py")
    catalog_name = "test-dynamic"
    catalog_url = "https://test-dynamic.com"
    mock_app_catalog_cr = mocker.Mock(name="MockAppCatalogCR")
    mock_app_catalog_cr.metadata = {"name": catalog_name}
    mock_app_catalog_cr.obj = {
        "spec": {
            "title": catalog_name,
            "storage": {
                "type": "helm",
                "URL": catalog_url,
            }
        }
    }
    mock_app_catalog_cr_type = mocker.Mock(name="MockAppCatalogCRType")
    mock_app_catalog_cr_type.return_value = mock_app_catalog_cr
    mocker.patch("pytest_helm_charts.giantswarm_app_platform.custom_resources.object_factory", autospec=True)
    pytest_helm_charts.giantswarm_app_platform.custom_resources.object_factory.return_value = mock_app_catalog_cr_type

    # run pytest with the following cmd args
    result = run_pytest(testdir, mocker, "test_giantswarm_app_platform.py::test_app_catalog_factory_fixture")

    mock_app_catalog_cr.create.assert_called_once()
    assert result.ret == 0


def test_app_factory_working(kube_cluster: Cluster, app_factory: AppFactoryFunc, testdir: Testdir, mocker: MockFixture):
    # patch appCatalogFactory
    catalog_name = "test-dynamic"
    catalog_url = "https://test-dynamic.com"

    def __mock_app_catalog_fact(name: str, url: Optional[str] = ""):
        mock_app_catalog_cr = mocker.Mock(name="MockAppCatalogCR")
        mock_app_catalog_cr.metadata = {"name": catalog_name}
        mock_app_catalog_cr.obj = {
            "spec": {
                "title": name,
                "storage": {
                    "type": "helm",
                    "URL": url,
                }
            }
        }
        return mock_app_catalog_cr

    mocker.patch("pytest_helm_charts.giantswarm_app_platform.app_catalog.app_catalog_factory_func")
    pytest_helm_charts.giantswarm_app_platform.app_catalog.app_catalog_factory_func.return_value = __mock_app_catalog_fact

    # patch AppCR returned typed
    app_name = "testing-app"
    mock_app_cr = mocker.Mock(name="MockAppCR")
    mock_app_cr.metadata = {"name": app_name}
    mock_app_cr.obj = {
        "spec": {
        }
    }
    mock_app_cr_type = mocker.Mock(name="MockAppCRType")
    mock_app_cr_type.return_value = mock_app_cr
    mocker.patch("pytest_helm_charts.giantswarm_app_platform.custom_resources.object_factory", autospec=True)
    pytest_helm_charts.giantswarm_app_platform.custom_resources.object_factory.return_value = mock_app_cr_type

    config_values: YamlDict = {
        "key1": {
            "key2": "my-val"
        }
    }
    mocker.patch("pytest_helm_charts.giantswarm_app_platform.app.ConfigMap")
    mocker.patch("pykube.objects.APIObject")
    test_app: pytest_helm_charts.AppCR = app_factory("test-app", "1.0.0", catalog_name, catalog_url,
                                                     "mu-custom-namespace", config_values)

# def test_app_loadtest_app_working(testdir: Testdir, mocker: MockFixture):
#     testdir.copy_example("examples/test_giantswarm_app_platform.py")
#     catalog_name = "test-dynamic"
#     catalog_url = "https://test-dynamic.com"
#     mock_app_catalog_cr = mocker.Mock(name="MockAppCR")
#     mock_app_catalog_cr.metadata = {"name": catalog_name}
#     mock_app_catalog_cr.obj = {
#         "spec": {
#             "title": catalog_name,
#             "storage": {
#                 "type": "helm",
#                 "URL": catalog_url,
#             }
#         }
#     }
#     mock_app_catalog_cr_type = mocker.Mock(name="MockAppCRType")
#     mock_app_catalog_cr_type.return_value = mock_app_catalog_cr
#     mocker.patch("pytest_helm_charts.giantswarm_app_platform.custom_resources.object_factory", autospec=True)
#     pytest_helm_charts.giantswarm_app_platform.custom_resources.object_factory.return_value = mock_app_catalog_cr_type
#
#     # run pytest with the following cmd args
#     result = run_pytest(testdir, mocker, "test_giantswarm_app_platform.py::test_app_catalog_factory_fixture")
#
#     mock_app_catalog_cr.create.assert_called_once()
#     assert result.ret == 0
