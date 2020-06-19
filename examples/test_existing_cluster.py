import pykube

from pytest_helm_charts.fixtures import Cluster
import logging

logger = logging.getLogger(__name__)


def test_api_working(kube_cluster: Cluster):
    assert kube_cluster.kube_client is not None
    assert len(pykube.Node.objects(kube_cluster.kube_client)) >= 1
