import pykube
from unittest.mock import create_autospec

from pytest_helm_charts.clusters import Cluster
from pytest_helm_charts.utils import proxy_http_request


def test_port_kwargs(kube_cluster: Cluster):
    mock_service = create_autospec(pykube.Service)

    proxy_http_request(kube_cluster.kube_client, mock_service, "GET", "/", port=8000)
