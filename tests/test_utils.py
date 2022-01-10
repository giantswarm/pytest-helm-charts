import unittest.mock
from typing import cast, Any, List, Dict

import pykube.exceptions
import pytest
from pykube import HTTPClient
from pykube.objects import NamespacedAPIObject
from pytest_mock import MockerFixture, MockFixture

from pytest_helm_charts.utils import wait_for_objects_condition
from pytest_helm_charts.k8s.job import make_job_object

MockCR = NamespacedAPIObject


def get_ready_objects_filter_mock(mocker: MockerFixture, k8s_api_call_results: List[Any]) -> unittest.mock.Mock:
    objects_mock = mocker.Mock(name="AppCR objects")
    filter_mock = mocker.Mock(name="AppCR objects->filter")
    objects_mock.filter.return_value = filter_mock
    filter_mock.get_by_name.side_effect = k8s_api_call_results
    return objects_mock


@pytest.mark.parametrize(
    "k8s_api_call_results,missing_ok,expected_result",
    [
        # One matching app found as expected
        ([{"status": "expected"}], False, 1),
        # One not matching app found and missing is OK
        ([{"status": "unexpected"}], True, TimeoutError),
        # One matching and one not and missing is OK
        ([{"status": "expected"}, {"status": "unexpected"}], True, TimeoutError),
        # One not matching app found and missing is not OK
        ([pykube.exceptions.ObjectDoesNotExist], False, pykube.exceptions.ObjectDoesNotExist),
        # One matching and one not found; missing is OK
        ([{"status": "expected"}, pykube.exceptions.ObjectDoesNotExist], True, TimeoutError),
        # One matching and one not found; missing is not OK
        ([{"status": "expected"}, pykube.exceptions.ObjectDoesNotExist], False, pykube.exceptions.ObjectDoesNotExist),
    ],
    ids=[
        "One matching app found as expected",
        "One not matching app found and missing is OK",
        "One matching and one not and missing is OK",
        "One not matching app found and missing is not OK",
        "One matching and one not found; missing is OK",
        "One matching and one not found; missing is not OK",
    ],
)
def test_wait_for_namespaced_objects_condition(
    mocker: MockFixture, k8s_api_call_results: List[Any], missing_ok: bool, expected_result: Any
) -> None:
    objects_mock = get_ready_objects_filter_mock(mocker, k8s_api_call_results)
    mocker.patch("tests.test_utils.MockCR")
    cast(unittest.mock.Mock, MockCR).objects.return_value = objects_mock

    check_fun_called = False

    def check_fun(obj: MockCR) -> bool:
        assert obj is not None
        nonlocal check_fun_called
        check_fun_called = True
        hacked_type_dict = cast(Dict[str, Any], obj)
        return hacked_type_dict["status"] == "expected"

    try:
        result = wait_for_objects_condition(
            cast(HTTPClient, None), MockCR, ["mock_cr"] * len(k8s_api_call_results), "test_ns", check_fun, 1, missing_ok
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
        assert result == k8s_api_call_results
        assert check_fun_called


def test_make_job_object() -> None:
    name_prefix = "test_name_prefix"
    namespace = "test_namespace"
    command = ["cmd1", "cmd2"]
    image: str = "quay.io/giantswarm/busybox:1.32.0"
    restart_policy: str = "OnFailure"
    backoff_limit: int = 6

    job = make_job_object(
        cast(HTTPClient, None), name_prefix, namespace, command, image, restart_policy, backoff_limit
    ).obj

    assert job["metadata"]["generateName"] == name_prefix
    assert job["metadata"]["namespace"] == namespace
    assert job["spec"]["backoffLimit"] == backoff_limit
    assert job["spec"]["template"]["spec"]["containers"][0]["name"] == f"{name_prefix}job"
    assert job["spec"]["template"]["spec"]["containers"][0]["image"] == image
    assert job["spec"]["template"]["spec"]["containers"][0]["command"] == command
    assert job["spec"]["template"]["spec"]["restartPolicy"] == restart_policy
