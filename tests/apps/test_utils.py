import unittest.mock
from typing import cast, Any

import pykube
import pytest
from pykube import ConfigMap, HTTPClient
from pytest_mock import MockFixture

import pytest_helm_charts
from pytest_helm_charts.giantswarm_app_platform.custom_resources import AppCR
from pytest_helm_charts.giantswarm_app_platform.entities import ConfiguredApp
from pytest_helm_charts.giantswarm_app_platform.utils import (
    delete_app,
    wait_for_apps_to_run,
    wait_for_app_to_be_deleted,
)
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


@pytest.mark.parametrize(
    "filter_result,side_effect,expected_del_result",
    [
        # App marked as deleted
        (
            {
                "status": {
                    "release": {"status": "deleted"},
                    "appVersion": "v1",
                }
            },
            None,
            True,
        ),
        # App already doesn't exist
        (None, pykube.exceptions.ObjectDoesNotExist, True),
        # Timeout, app exists with unexpected state
        (
            {
                "status": {
                    "release": {"status": "deployed"},
                    "appVersion": "v1",
                }
            },
            None,
            False,
        ),
    ],
    ids=["App marked as deleted", "App already doesn't exist", "Timeout, app exists with unexpected state"],
)
def test_wait_for_app_to_be_deleted(
    mocker: MockFixture, filter_result: Any, side_effect: Any, expected_del_result: bool
) -> None:
    objects_mock = get_ready_objects_filter_mock(filter_result, mocker, side_effect)
    mocker.patch("pytest_helm_charts.giantswarm_app_platform.utils.AppCR")
    cast(unittest.mock.Mock, pytest_helm_charts.giantswarm_app_platform.utils.AppCR).objects.return_value = objects_mock

    try:
        del_result = wait_for_app_to_be_deleted(cast(HTTPClient, None), "test_app", "test_ns", 1)
    except TimeoutError:
        del_result = False
    assert del_result == expected_del_result
