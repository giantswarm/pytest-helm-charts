import unittest.mock

import yaml
from pytest_mock import MockFixture
from tests.helper import get_mock_app_cr, get_mock_app_catalog_cr

import pytest_helm_charts
from pytest_helm_charts.clusters import Cluster
from pytest_helm_charts.giantswarm_app_platform.app import AppFactoryFunc
from pytest_helm_charts.giantswarm_app_platform.custom_resources import AppCR
from pytest_helm_charts.utils import YamlDict
from tests.conftest import MockAppPlatformCRs


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
