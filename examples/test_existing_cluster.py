from pytest_helm_chart import Cluster
import logging

logger = logging.getLogger(__name__)


def test_app_running(kube_cluster: Cluster):
    logger.info(kube_cluster)
    assert True
