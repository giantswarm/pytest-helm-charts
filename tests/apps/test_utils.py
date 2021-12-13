import unittest.mock
from typing import cast, Any, List

import pykube
import pytest
from pykube import ConfigMap, HTTPClient
from pytest_mock import MockFixture

import pytest_helm_charts
from pytest_helm_charts.giantswarm_app_platform.app import (
    wait_for_apps_to_run,
    wait_for_app_to_be_deleted,
    delete_app,
    ConfiguredApp,
    AppCR,
)
from tests.test_utils import get_ready_objects_filter_mock


def test_delete_app(mocker: MockFixture) -> None:
    app_cr = mocker.MagicMock(spec=AppCR)
    cm = mocker.MagicMock(spec=ConfigMap)
    configured_app = ConfiguredApp(app=app_cr, app_cm=cm)

    delete_app(configured_app)

    app_cr.delete.assert_called_once_with()
    cm.delete.assert_called_once_with()


class MockAppCR:
    def __init__(self, status: str):
        self.obj = {
            "status": {
                "release": {"status": status},
                "appVersion": "v1",
            },
        }


def test_wait_for_apps_to_run(mocker: MockFixture) -> None:
    app_mock = MockAppCR("deployed")
    objects_mock = get_ready_objects_filter_mock(mocker, [app_mock])
    mocker.patch("pytest_helm_charts.giantswarm_app_platform.app.AppCR")
    cast(unittest.mock.Mock, pytest_helm_charts.giantswarm_app_platform.app.AppCR).objects.return_value = objects_mock

    result = wait_for_apps_to_run(cast(HTTPClient, None), ["test_app"], "test_ns", 10)
    assert app_mock == result[0]


@pytest.mark.parametrize(
    "k8s_api_call_results,expected_del_result",
    [
        # App marked as deleted
        ([MockAppCR("deleted")], True),
        # App already doesn't exist
        ([pykube.exceptions.ObjectDoesNotExist], True),
        # Timeout, app exists with unexpected state
        ([MockAppCR("deployed")], False),
    ],
    ids=["App marked as deleted", "App already doesn't exist", "Timeout, app exists with unexpected state"],
)
def test_wait_for_app_to_be_deleted(
    mocker: MockFixture, k8s_api_call_results: List[Any], expected_del_result: bool
) -> None:
    objects_mock = get_ready_objects_filter_mock(mocker, k8s_api_call_results)
    mocker.patch("pytest_helm_charts.giantswarm_app_platform.app.AppCR")
    cast(unittest.mock.Mock, pytest_helm_charts.giantswarm_app_platform.app.AppCR).objects.return_value = objects_mock

    try:
        del_result = wait_for_app_to_be_deleted(cast(HTTPClient, None), "test_app", "test_ns", 1)
    except TimeoutError:
        del_result = False
    assert del_result == expected_del_result
