from pykube import Service

from pytest_helm_charts.clusters import Cluster
from pytest_helm_charts.giantswarm_app_platform.apps.http_testing import StormforgerLoadAppFactoryFunc
from pytest_helm_charts.utils import wait_for_deployments_to_run, proxy_http_get


def test_stormforger_load_app_creation(
    kube_cluster: Cluster, stormforger_load_app_factory: StormforgerLoadAppFactoryFunc
) -> None:
    """ This test deploys stormforger_load_app and checks if it response to basic requests.
    To make this example run, you need a ready cluster with Giant Swarm App Platform.
    The easiest way to create it is to run: `kube-app-testing.sh -j`.
    """
    loadtest_app = stormforger_load_app_factory(1, "test.local", None)
    assert loadtest_app.app is not None
    wait_for_deployments_to_run(kube_cluster.kube_client, [loadtest_app.app.name], loadtest_app.app.namespace, 60)
    srv: Service = Service.objects(kube_cluster.kube_client, loadtest_app.app.namespace).get_by_name(
        loadtest_app.app.name
    )
    assert srv is not None
    res = proxy_http_get(kube_cluster.kube_client, srv, "/", headers={"Host": "test.local"})
    assert res is not None
    assert res.ok
    assert res.status_code == 200
    assert res.text.startswith("GET / HTTP/1.1\r\nHost: test.local\r\n")
