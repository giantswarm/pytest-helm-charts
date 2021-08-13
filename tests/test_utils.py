import unittest.mock
from typing import cast, Any

import pykube.exceptions
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
        ({"status": "expected"}, None, False, 1),
        # One not matching app found and missing is OK
        ({"status": "unexpected"}, None, True, TimeoutError),
        # One not matching app found and missing is not OK
        ({"status": "unexpected"}, pykube.exceptions.ObjectDoesNotExist, False, pykube.exceptions.ObjectDoesNotExist),
    ],
    ids=[
        "One matching app found as expected",
        "One not matching app found and missing is OK",
        "One not matching app found and missing is not OK",
    ],
)
def test_wait_for_namespaced_objects_condition(
    mocker: MockFixture, filter_result: Any, side_effect: Any, missing_ok: bool, expected_result: Any
) -> None:
    objects_mock = get_ready_objects_filter_mock(filter_result, mocker, side_effect)
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
    except Exception as e:
        if (expected_result is TimeoutError and type(e) is TimeoutError) or (
            expected_result is pykube.exceptions.ObjectDoesNotExist and type(e) is pykube.exceptions.ObjectDoesNotExist
        ):
            # we have the expected exception
            pass
        else:
            raise
    else:
        assert type(expected_result) is int
        assert len(result) == expected_result
        assert filter_result == result[0].obj
        assert check_fun_called
