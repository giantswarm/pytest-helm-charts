import unittest.mock

import yaml
from _pytest.pytester import Testdir
from pytest_mock import MockFixture

import pytest_helm_charts.giantswarm_app_platform.app_catalog
import pytest_helm_charts.giantswarm_app_platform.custom_resources
from pytest_helm_charts.clusters import Cluster
from pytest_helm_charts.giantswarm_app_platform.app import AppFactoryFunc
from pytest_helm_charts.giantswarm_app_platform.custom_resources import AppCR
from pytest_helm_charts.utils import YamlDict
from tests.conftest import MockAppPlatformCRs
from tests.helper import run_pytest


def get_mock_app_catalog_cr(mocker: MockFixture, catalog_name: str, catalog_url: str) -> unittest.mock.Mock:
    mock_app_catalog_cr = mocker.Mock(name=f"MockAppCatalogCR-{catalog_name}")
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
    return mock_app_catalog_cr


def get_mock_app_cr(mocker: MockFixture, app_name: str) -> unittest.mock.Mock:
    mock_app_cr = mocker.Mock(name=f"MockAppCR-{app_name}")
    mock_app_cr.metadata = {"name": app_name}
    mock_app_cr.obj = {
        "spec": {
        }
    }
    return mock_app_cr


def test_app_catalog_working(testdir: Testdir, mocker: MockFixture):
    testdir.copy_example("examples/test_giantswarm_app_platform.py")
    catalog_name = "test-dynamic"
    catalog_url = "https://test-dynamic.com"

    mock_app_catalog_cr = get_mock_app_catalog_cr(mocker, catalog_name, catalog_url)
    mock_app_catalog_cr_type = mocker.Mock(name="MockAppCatalogCRType")
    mock_app_catalog_cr_type.return_value = mock_app_catalog_cr
    mocker.patch("pytest_helm_charts.giantswarm_app_platform.custom_resources.object_factory", autospec=True)
    pytest_helm_charts.giantswarm_app_platform.custom_resources.object_factory.return_value = mock_app_catalog_cr_type

    # run pytest with the following cmd args
    result = run_pytest(testdir, mocker, "test_giantswarm_app_platform.py::test_app_catalog_factory_fixture")

    mock_app_catalog_cr.create.assert_called_once()
    assert result.ret == 0


def test_app_factory_working(kube_cluster: Cluster, app_factory: AppFactoryFunc, mocker: MockFixture,
                             gs_app_platform_crs: MockAppPlatformCRs):
    catalog_name = "test-dynamic"
    catalog_url = "https://test-dynamic.com"
    app_name = "testing-app"
    app_namespace = "my-namespace"

    mock_app_cr = get_mock_app_cr(mocker, app_name)
    mock_app_catalog_cr = get_mock_app_catalog_cr(mocker, catalog_name, catalog_url)
    gs_app_platform_crs.app_catalog_cr_factory.return_value = mock_app_catalog_cr
    gs_app_platform_crs.app_cr_factory.return_value = mock_app_cr

    config_values: YamlDict = {
        "key1": {
            "key2": "my-val"
        }
    }
    mocker.patch("pytest_helm_charts.giantswarm_app_platform.app.ConfigMap")
    test_app: AppCR = app_factory(app_name, "1.0.0", catalog_name, catalog_url, app_namespace, config_values)

    # assert that configMap was created for the app
    cm: unittest.mock.Mock = pytest_helm_charts.giantswarm_app_platform.app.ConfigMap
    cm.assert_called_once()
    assert cm.call_args_list[0].args[0] == kube_cluster.kube_client
    assert cm.call_args_list[0].args[1]["apiVersion"] == "v1"
    assert cm.call_args_list[0].args[1]["kind"] == "ConfigMap"
    assert cm.call_args_list[0].args[1]["metadata"] == {
        "name": app_name + "-testing-user-config",
        "namespace": app_namespace
    }
    assert yaml.load(cm.call_args_list[0].args[1]["data"]["values"]) == config_values

    # assert that app object was called with create()
    assert test_app == mock_app_cr
    mock_app_cr.create.assert_called_once()

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
