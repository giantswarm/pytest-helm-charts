import unittest.mock
from typing import cast

from pykube import ConfigMap, HTTPClient
from pytest_mock import MockFixture

import pytest_helm_charts
from pytest_helm_charts.giantswarm_app_platform.custom_resources import AppCR
from pytest_helm_charts.giantswarm_app_platform.entities import ConfiguredApp
from pytest_helm_charts.giantswarm_app_platform.utils import delete_app, wait_for_apps_to_run


def test_delete_app(mocker: MockFixture) -> None:
    app_cr = mocker.MagicMock(spec=AppCR)
    cm = mocker.MagicMock(spec=ConfigMap)
    configured_app = ConfiguredApp(app=app_cr, app_cm=cm)

    delete_app(configured_app)

    app_cr.delete.assert_called_once_with()
    cm.delete.assert_called_once_with()


def test_wait_for_apps_to_run(mocker: MockFixture) -> None:
    filter_mock = mocker.Mock(name="AppCR filter result")
    objects_mock = mocker.Mock(name="AppCR objects result")
    objects_mock.filter.return_value = filter_mock
    app_mock = mocker.MagicMock(name="test mock app")
    app_mock.obj = {
        "status": {
            "release": {"status": "deployed"},
            "appVersion": "v1",
        }
    }
    filter_mock.get_by_name.return_value = app_mock
    mocker.patch("pytest_helm_charts.giantswarm_app_platform.utils.AppCR")
    cast(unittest.mock.Mock, pytest_helm_charts.giantswarm_app_platform.utils.AppCR).objects.return_value = objects_mock

    result = wait_for_apps_to_run(cast(HTTPClient, None), ["test_app"], "test_ns", 10)
    assert app_mock == result[0]
