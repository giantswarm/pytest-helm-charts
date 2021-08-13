import unittest.mock
from typing import cast, Any

import pytest
from pykube import HTTPClient
from pykube.objects import NamespacedAPIObject
from pytest_mock import MockerFixture, MockFixture

from pytest_helm_charts.utils import wait_for_namespaced_objects_condition

MockCR = NamespacedAPIObject


def get_ready_objects_filter_mock(
    filter_result: Any, mocker: MockerFixture, side_effect: Any = None
) -> unittest.mock.Mock:
    objects_mock = mocker.Mock(name="AppCR objects")
    filter_mock = mocker.Mock(name="AppCR objects->filter")
    obj_mock = mocker.MagicMock(name="test mock app")
    obj_mock.obj = filter_result
    objects_mock.filter.return_value = filter_mock
    if side_effect is not None:
        filter_mock.get_by_name.side_effect = side_effect
    else:
        filter_mock.get_by_name.return_value = obj_mock
    return objects_mock


@pytest.mark.parametrize(
    "filter_result,side_effect,missing_ok,expected_result",
    [
        # One matching app found as expected
        ({"status": "expected"}, None, False, True),
        # One not matching app found and missing is OK
        ({"status": "unexpected"}, None, True, False),
    ],
    ids=["One matching app found as expected", "One not matching app found and missing is OK"],
)
def test_wait_for_namespaced_objects_condition(
    mocker: MockFixture, filter_result: Any, side_effect: Any, missing_ok: bool, expected_result: bool
) -> None:
    objects_mock = get_ready_objects_filter_mock(filter_result, mocker)
    mocker.patch("tests.test_utils.MockCR")
    cast(unittest.mock.Mock, MockCR).objects.return_value = objects_mock

    check_fun_called = False

    def check_fun(obj: MockCR) -> bool:
        assert obj is not None
        nonlocal check_fun_called
        check_fun_called = True
        return obj.obj["status"] == "expected"

    try:
        result = wait_for_namespaced_objects_condition(
            cast(HTTPClient, None), MockCR, ["mock_cr_1"], "test_ns", check_fun, 1, missing_ok
        )
    except TimeoutError:
        pass
    else:
        assert filter_result == result[0].obj
        assert check_fun_called
