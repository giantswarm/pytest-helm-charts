import logging
import unittest.mock
from typing import cast, Type

import pykube
import pytest
from pykube import ConfigMap, Namespace
from pytest_mock import MockerFixture

import pytest_helm_charts
import pytest_helm_charts.k8s.fixtures
import pytest_helm_charts.k8s.namespace
import pytest_helm_charts.fixtures
import pytest_helm_charts.giantswarm_app_platform.app
import pytest_helm_charts.giantswarm_app_platform.fixtures
from pytest_helm_charts.clusters import Cluster
from pytest_helm_charts.giantswarm_app_platform.app import AppFactoryFunc, ConfiguredApp
from pytest_helm_charts.giantswarm_app_platform.catalog import CatalogFactoryFunc
from pytest_helm_charts.utils import YamlDict, T

logger = logging.getLogger(__name__)

CATALOG_NAME = "my_catalog"
CATALOG_NAMESPACE = "my_namespace"
CATALOG_URL = "http://invalid.host:1234"


def mock_final_object_cleanup(mocker: MockerFixture, obj_type: Type[T]) -> None:
    if type(getattr(obj_type, "objects")) is mocker.MagicMock:
        return
    get_or_none_call = mocker.MagicMock(name="get_or_none_call")
    get_or_none_call.get_or_none = mocker.MagicMock(name="get_or_none_res")
    get_or_none_call.get_or_none.return_value = None
    objects_call = mocker.MagicMock(name="custom_objects_call")
    objects_call.return_value = get_or_none_call
    delete_call = mocker.MagicMock(name="delete_call")
    delete_call.return_value = True
    setattr(obj_type, "objects", objects_call)
    setattr(obj_type, "delete", delete_call)


def mock_final_configured_app_cleanup(mocker: MockerFixture) -> None:
    mock_final_object_cleanup(mocker, Namespace)
    mock_final_object_cleanup(mocker, ConfigMap)
    mock_final_object_cleanup(mocker, pytest_helm_charts.giantswarm_app_platform.app.AppCR)


def test_app_factory_working(kube_cluster: Cluster, app_factory: AppFactoryFunc, mocker: MockerFixture) -> None:
    app_name = "testing-app"
    app_namespace = "my-namespace"
    app_version = "1.0.0"

    config_values: YamlDict = {"key1": {"key2": "my-val"}}
    mock_final_configured_app_cleanup(mocker)
    mocker.patch("pytest_helm_charts.giantswarm_app_platform.catalog.CatalogCR.create")
    mocker.patch("pytest_helm_charts.giantswarm_app_platform.app.AppCR")
    mocker.patch("pytest_helm_charts.giantswarm_app_platform.app.ConfigMap")
    mocker.patch("pytest_helm_charts.giantswarm_app_platform.app.wait_for_apps_to_run")
    mocker.patch("pytest_helm_charts.k8s.fixtures.ensure_namespace_exists")
    cast(unittest.mock.Mock, pytest_helm_charts.k8s.fixtures.ensure_namespace_exists).return_value = (
        mocker.MagicMock(),
        True,
    )
    test_configured_app: ConfiguredApp = app_factory(
        app_name,
        app_version,
        CATALOG_NAME,
        CATALOG_NAMESPACE,
        CATALOG_URL,
        namespace=app_namespace,
        deployment_namespace=app_namespace,
        config_values=config_values,
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
    cast(unittest.mock.Mock, app_cm.create).assert_called_once()

    # assert that app was created
    assert cast(unittest.mock.Mock, pytest_helm_charts.k8s.fixtures.ensure_namespace_exists).call_count == 2
    cast(unittest.mock.Mock, pytest_helm_charts.k8s.fixtures.ensure_namespace_exists).assert_any_call(
        kube_cluster.kube_client, app_namespace, None, None
    )
    cast(unittest.mock.Mock, pytest_helm_charts.k8s.fixtures.ensure_namespace_exists).assert_any_call(
        kube_cluster.kube_client, CATALOG_NAMESPACE, None, None
    )
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
                "catalog": CATALOG_NAME,
                "catalogNamespace": CATALOG_NAMESPACE,
                "version": app_version,
                "kubeConfig": {"inCluster": True},
                "name": app_name,
                "namespace": app_namespace,
                "config": {"configMap": {"name": app_name + "-testing-user-config", "namespace": app_namespace}},
            },
        },
    )
    cast(unittest.mock.Mock, test_configured_app.app.create).assert_called_once()
    cast(
        unittest.mock.Mock, pytest_helm_charts.giantswarm_app_platform.app.wait_for_apps_to_run
    ).assert_called_once_with(kube_cluster.kube_client, [app_name], app_namespace, 60)


def mock_final_catalog_cleanup(mocker: MockerFixture) -> None:
    mock_final_object_cleanup(mocker, pykube.Namespace)
    mock_final_object_cleanup(mocker, pytest_helm_charts.giantswarm_app_platform.catalog.CatalogCR)


def test_catalog_factory_working(catalog_factory: CatalogFactoryFunc, mocker: MockerFixture) -> None:
    mock_final_catalog_cleanup(mocker)
    mocker.patch.object(pytest_helm_charts.giantswarm_app_platform.catalog.CatalogCR, "create")
    catalog = catalog_factory(CATALOG_NAME, CATALOG_NAMESPACE, CATALOG_URL)

    expected_catalog_obj = {
        "apiVersion": "application.giantswarm.io/v1alpha1",
        "kind": "Catalog",
        "metadata": {
            "name": CATALOG_NAME,
            "namespace": CATALOG_NAMESPACE,
        },
        "spec": {
            "description": "Catalog for testing.",
            "storage": {"URL": CATALOG_URL, "type": "helm"},
            "title": CATALOG_NAME,
            "logoURL": "https://my-org.github.com/logo.png",
            "repositories": [
                {
                    "URL": CATALOG_URL,
                    "type": "helm",
                }
            ],
        },
    }
    assert catalog.obj == expected_catalog_obj
    # catalog should be created at most once (might have been already requested in another test)
    assert (
        cast(
            unittest.mock.Mock, pytest_helm_charts.giantswarm_app_platform.catalog.CatalogCR.create  # type: ignore
        ).call_count
        <= 1
    )


def test_double_create_the_same_catalog(catalog_factory: CatalogFactoryFunc, mocker: MockerFixture) -> None:
    mock_final_catalog_cleanup(mocker)
    mocker.patch.object(pytest_helm_charts.giantswarm_app_platform.catalog.CatalogCR, "create")
    catalog_factory(CATALOG_NAME, CATALOG_NAMESPACE, CATALOG_URL)
    # ask the factory the create the same catalog once again
    catalog_factory(CATALOG_NAME, CATALOG_NAMESPACE, CATALOG_URL)
    # catalog should be created at most once (might have been already requested in another test)
    assert (
        cast(
            unittest.mock.Mock, pytest_helm_charts.giantswarm_app_platform.catalog.CatalogCR.create  # type: ignore
        ).call_count
        <= 1
    )


def test_create_the_same_catalog_name_diff_url(catalog_factory: CatalogFactoryFunc, mocker: MockerFixture) -> None:
    mock_final_catalog_cleanup(mocker)
    mocker.patch.object(pytest_helm_charts.giantswarm_app_platform.catalog.CatalogCR, "create")

    catalog_cr = catalog_factory(CATALOG_NAME, CATALOG_NAMESPACE, CATALOG_URL)
    catalog_cr.delete = mocker.Mock()  # type: ignore
    # ask the factory the create the same catalog once again, but with changed URL; this should raise an error
    with pytest.raises(ValueError):
        catalog_factory(CATALOG_NAME, CATALOG_NAMESPACE, CATALOG_URL + "change")
