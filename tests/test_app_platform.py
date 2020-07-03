import logging
import unittest.mock

import yaml
from pytest_mock import MockFixture

import pytest_helm_charts
from pytest_helm_charts.clusters import Cluster
from pytest_helm_charts.giantswarm_app_platform.app import AppFactoryFunc
from pytest_helm_charts.giantswarm_app_platform.custom_resources import AppCR
from pytest_helm_charts.utils import YamlDict

logger = logging.getLogger(__name__)


def test_app_factory_working(kube_cluster: Cluster, app_factory: AppFactoryFunc, mocker: MockFixture):
    catalog_name = "test-dynamic"
    catalog_url = "https://test-dynamic.com"
    app_name = "testing-app"
    app_namespace = "my-namespace"

    config_values: YamlDict = {
        "key1": {
            "key2": "my-val"
        }
    }
    mocker.patch("pytest_helm_charts.giantswarm_app_platform.app_catalog.AppCatalogCR.create")
    mocker.patch("pytest_helm_charts.giantswarm_app_platform.app.AppCR.create")
    mocker.patch("pytest_helm_charts.giantswarm_app_platform.app.ConfigMap", autospec=True)
    cm: unittest.mock.Mock = pytest_helm_charts.giantswarm_app_platform.app.ConfigMap
    test_app: AppCR = app_factory(app_name, "1.0.0", catalog_name, catalog_url, app_namespace, config_values)

    # assert that configMap was created for the app
    cm.assert_called_once()
    logger.info(f"len: {len(cm.call_args_list)}")
    logger.info(f"list[0]: {cm.call_args_list[0]}")
    logger.info(f"list[0].args[0]: {cm.call_args_list[0].args[0]}")
    logger.info(f"list[0].args[1]: {cm.call_args_list[0].args[1]}")
    assert cm.call_args_list[0].args[0] == kube_cluster.kube_client
    assert cm.call_args_list[0].args[1]["apiVersion"] == "v1"
    assert cm.call_args_list[0].args[1]["kind"] == "ConfigMap"
    assert cm.call_args_list[0].args[1]["metadata"] == {
        "name": app_name + "-testing-user-config",
        "namespace": app_namespace
    }
    assert yaml.load(cm.call_args_list[0].args[1]["data"]["values"]) == config_values
    # TODO: assert cm.create() called once

    # assert that app object was called with create()
    # TODO: assert App YAML passed correctly
    test_app.create.assert_called_once()
