import unittest.mock

import pytest
from pykube import HTTPClient
from pytest_mock import MockFixture

from pytest_helm_charts.clusters import Cluster
from pytest_helm_charts.fixtures import ConfigFactoryFunction

pytest_plugins = [
    'pytester'
]


class MockCluster(Cluster):
    """Implementation of [Cluster](Cluster) that uses mock HTTPClient
    """

    def __init__(self, mocker: MockFixture):
        super().__init__()
        self.__mocker = mocker

    def create(self) -> HTTPClient:
        mock_client = self.__mocker.MagicMock(name="MockHTTPClient")
        self._kube_client = mock_client
        return self._kube_client

    def destroy(self) -> None:
        if self._kube_client is None:
            return
        self._kube_client = None


@pytest.fixture(scope="module")
def kube_cluster(cluster_type: str,
                 session_mocker: MockFixture,
                 _existing_cluster_factory: ConfigFactoryFunction,
                 _kind_cluster_factory: ConfigFactoryFunction,
                 _giantswarm_cluster_factory: ConfigFactoryFunction) -> Cluster:
    cluster = MockCluster(session_mocker)
    cluster.create()
    return cluster


class MockAppPlatformCRs:
    def __init__(self, mocker: MockFixture):
        self.app_cr_factory: unittest.mock.Mock = mocker.Mock(name="MockAppCRType")
        self.app_catalog_cr_factory: unittest.mock.Mock = mocker.Mock(name="MockAppCatalogCRType")


@pytest.fixture(scope="module")
def gs_app_platform_crs(kube_cluster: Cluster, session_mocker: MockFixture) -> MockAppPlatformCRs:
    result = MockAppPlatformCRs(session_mocker)
    return result
