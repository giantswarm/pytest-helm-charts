import logging
import unittest.mock
from typing import cast

from pykube import ConfigMap
from pytest_mock import MockFixture

import pytest_helm_charts
from pytest_helm_charts.clusters import Cluster
from pytest_helm_charts.giantswarm_app_platform.app import AppFactoryFunc, ConfiguredApp
from pytest_helm_charts.utils import YamlDict

logger = logging.getLogger(__name__)


def test_app_factory_working(kube_cluster: Cluster, app_factory: AppFactoryFunc, mocker: MockFixture):
    catalog_name = "test-dynamic"
    catalog_url = "https://test-dynamic.com"
    app_name = "testing-app"
    app_namespace = "my-namespace"
    app_version = "1.0.0"

    config_values: YamlDict = {"key1": {"key2": "my-val"}}
    mocker.patch("pytest_helm_charts.giantswarm_app_platform.app_catalog.AppCatalogCR.create")
    mocker.patch("pytest_helm_charts.giantswarm_app_platform.app.AppCR", autospec=True)
    mocker.patch("pytest_helm_charts.giantswarm_app_platform.app.ConfigMap", autospec=True)
    mocker.patch("pytest_helm_charts.giantswarm_app_platform.app.wait_for_apps_to_run", autospec=True)
    test_configured_app: ConfiguredApp = app_factory(
        app_name, app_version, catalog_name, catalog_url, namespace=app_namespace, config_values=config_values
    )

    # assert that configMap was created for the app
    cm = cast(unittest.mock.Mock, pytest_helm_charts.giantswarm_app_platform.app.ConfigMap)
    cm.assert_called_once_with(
        kube_cluster.kube_client,
        {
            "apiVersion": "v1",
            "kind": "ConfigMap",
            "metadata": {"name": app_name + "-testing-user-config", "namespace": app_namespace},
            "data": {"values": "key1:\n  key2: my-val\n"},
        },
    )
    assert test_configured_app.app_cm is not None
    app_cm: ConfigMap = test_configured_app.app_cm
    cast(unittest.mock.Mock, app_cm.create).assert_called_once_with()

    # assert that app was created
    app_cr = cast(unittest.mock.Mock, pytest_helm_charts.giantswarm_app_platform.app.AppCR)
    app_cr.assert_called_once_with(
        kube_cluster.kube_client,
        {
            "apiVersion": "application.giantswarm.io/v1alpha1",
            "kind": "App",
            "metadata": {
                "name": app_name,
                "namespace": app_namespace,
                "labels": {"app": "testing-app", "app-operator.giantswarm.io/version": "0.0.0"},
            },
            "spec": {
                "catalog": catalog_name,
                "version": app_version,
                "kubeConfig": {"inCluster": True},
                "name": app_name,
                "namespace": app_namespace,
                "namespaceConfig": {"annotations": {}, "labels": {}},
                "config": {"configMap": {"name": app_name + "-testing-user-config", "namespace": app_namespace}},
            },
        },
    )
    cast(unittest.mock.Mock, test_configured_app.app.create).assert_called_once_with()
    cast(
        unittest.mock.Mock, pytest_helm_charts.giantswarm_app_platform.app.wait_for_apps_to_run
    ).assert_called_once_with(kube_cluster.kube_client, [app_name], app_namespace, 60)
