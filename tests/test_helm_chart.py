# -*- coding: utf-8 -*-
from _pytest.monkeypatch import MonkeyPatch
from _pytest.pytester import Testdir
from pykube import KubeConfig

from pytest_helm_charts.clusters import Cluster


class MockSession:

    def close(self):
        pass


class MockKubeConfig:
    path: str

    def __init__(self, path: str) -> None:
        self.path = path


class MockHTTPClient:
    kube_config: MockKubeConfig
    session: MockSession

    def __init__(self, kube_config: MockKubeConfig) -> None:
        self.kube_config = kube_config
        self.session = MockSession()


def test_existing_cluster_example(testdir: Testdir, monkeypatch: MonkeyPatch):
    """Make sure that existing cluster is created using the correct config file."""

    testdir.copy_example("examples/test_existing_cluster.py")

    def mock_kube_config(path):
        return MockKubeConfig(path)

    def mock_http_client(_, kube_config):
        return MockHTTPClient(kube_config)

    monkeypatch.setattr(KubeConfig, "from_file", mock_kube_config)
    monkeypatch.setattr(Cluster, "create_http_client_from_kube_config", mock_http_client)

    # run pytest with the following cmd args
    result = testdir.runpytest(
        '--cluster-type',
        'existing',
        '--kube-config',
        '/tmp/kat_test/kube.config',
        '-v'
    )

    # fnmatch_lines does an assertion internally
    #result.stdout.fnmatch_lines([
    #    '*::test_sth PASSED*',
    #])

    # make sure that that we get a '0' exit code for the testsuite
    assert result.ret == 0

