from typing import Dict, Any

import pykube
import pytest
from pytest_mock import MockFixture

from pytest_helm_charts.utils import proxy_http_request


@pytest.mark.parametrize(
    "call_kwargs,expected_request_kwargs",
    [
        # empty input kwargs - default service port should be used
        ({}, {"url": "services/test_service:9090/proxy//", "namespace": "test_namespace", "version": "1"}),
        # override the default port, should be included in url
        (
            {"port": 8080},
            {"url": "services/test_service:8080/proxy//", "namespace": "test_namespace", "version": "1"},
        ),
    ],
)
def test_port_kwargs(mocker: MockFixture, call_kwargs: Dict[str, Any], expected_request_kwargs: Dict[str, Any]) -> None:
    mock_client = mocker.MagicMock(spec=pykube.http.HTTPClient)
    mock_service = mocker.MagicMock(spec=pykube.objects.Service)
    type(mock_service).name = mocker.PropertyMock(return_value="test_service")
    type(mock_service).namespace = mocker.PropertyMock(return_value="test_namespace")
    type(mock_service).version = mocker.PropertyMock(return_value="1")
    type(mock_service).obj = mocker.PropertyMock(return_value={"spec": {"ports": [{"port": 9090}]}})

    proxy_http_request(mock_client, mock_service, "GET", "/", **call_kwargs)

    request = mock_client.request
    assert request.called
    assert request.call_args_list[0][0] == ("GET",)
    assert request.call_args_list[0][1] == expected_request_kwargs
