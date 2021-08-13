import unittest.mock
from typing import cast, Any

from pykube import HTTPClient
from pykube.objects import NamespacedAPIObject
from pytest_mock import MockerFixture

from pytest_helm_charts.utils import wait_for_namespaced_objects_condition

MockCR = NamespacedAPIObject


def get_ready_objects_filter_mock(filter_result: Any, mocker: MockerFixture) -> unittest.mock.Mock:
    objects_mock = mocker.Mock(name="AppCR objects")
    filter_mock = mocker.Mock(name="AppCR objects->filter")
    obj_mock = mocker.MagicMock(name="test mock app")
    obj_mock.obj = filter_result
    objects_mock.filter.return_value = filter_mock
    filter_mock.get_by_name.return_value = obj_mock
    return objects_mock


def test_wait_for_namespaced_objects_condition(mocker: MockerFixture) -> None:
    obj_mock_obj_property = {
        "status": {
            "release": {"status": "deployed"},
            "appVersion": "v1",
        }
    }
    objects_mock = get_ready_objects_filter_mock(obj_mock_obj_property, mocker)
    mocker.patch("tests.test_utils.MockCR")
    cast(unittest.mock.Mock, MockCR).objects.return_value = objects_mock

    check_fun_called = False

    def check_fun(obj: MockCR) -> bool:
        assert obj is not None
        nonlocal check_fun_called
        check_fun_called = True
        return True

    result = wait_for_namespaced_objects_condition(
        cast(HTTPClient, None), MockCR, ["mock_cr_1"], "test_ns", check_fun, 10, False
    )

    assert obj_mock_obj_property == result[0].obj
    assert check_fun_called
