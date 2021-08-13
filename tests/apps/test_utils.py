import unittest.mock
from typing import cast

from pykube import ConfigMap, HTTPClient
from pytest_mock import MockFixture

import pytest_helm_charts
from pytest_helm_charts.giantswarm_app_platform.custom_resources import AppCR
from pytest_helm_charts.giantswarm_app_platform.entities import ConfiguredApp
from pytest_helm_charts.giantswarm_app_platform.utils import delete_app, wait_for_apps_to_run
from tests.test_utils import get_ready_objects_filter_mock


def test_delete_app(mocker: MockFixture) -> None:
    app_cr = mocker.MagicMock(spec=AppCR)
    cm = mocker.MagicMock(spec=ConfigMap)
    configured_app = ConfiguredApp(app=app_cr, app_cm=cm)

    delete_app(configured_app)

    app_cr.delete.assert_called_once_with()
    cm.delete.assert_called_once_with()


def test_wait_for_apps_to_run(mocker: MockFixture) -> None:
    app_mock_obj_property = {
        "status": {
            "release": {"status": "deployed"},
            "appVersion": "v1",
        }
    }
    objects_mock = get_ready_objects_filter_mock(app_mock_obj_property, mocker)
    mocker.patch("pytest_helm_charts.giantswarm_app_platform.utils.AppCR")
    cast(unittest.mock.Mock, pytest_helm_charts.giantswarm_app_platform.utils.AppCR).objects.return_value = objects_mock

    result = wait_for_apps_to_run(cast(HTTPClient, None), ["test_app"], "test_ns", 10)
    assert app_mock_obj_property == result[0].obj
