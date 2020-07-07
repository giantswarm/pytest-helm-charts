"""This module introduces classes for handling different clusters."""
from abc import ABC, abstractmethod
from typing import Optional

from pykube import HTTPClient, KubeConfig


class Cluster(ABC):
    """Represents an abstract cluster."""

    _kube_client: Optional[HTTPClient]

    def __init__(self):
        self._kube_client = None

    @abstractmethod
    def create(self) -> HTTPClient:
        """Creates an instance of a cluster and returns HTTPClient to connect to it."""
        raise NotImplementedError

    @abstractmethod
    def destroy(self) -> None:
        """Destroys the cluster created earlier with a call to [create](Cluster.create)."""
        raise NotImplementedError

    @property
    def kube_client(self) -> Optional[HTTPClient]:
        """Returns the HTTP client you can use to access Kubernetes API of the cluster under test.

        Please refer to [pykube](https://pykube.readthedocs.io/en/latest/api/pykube.html) to get docs
        for [HTTPClient](https://pykube.readthedocs.io/en/latest/api/pykube.html#pykube.http.HTTPClient).
        """
        return self._kube_client


class ExistingCluster(Cluster):
    """Implementation of [Cluster](Cluster) that uses kube.config
    for an existing cluster.
    """

    kube_config_path: str

    def __init__(self, kube_config_path: str) -> None:
        super().__init__()
        self.kube_config_path = kube_config_path

    def create(self) -> HTTPClient:
        kube_config = KubeConfig.from_file(self.kube_config_path)
        self._kube_client = HTTPClient(kube_config)
        return self._kube_client

    def destroy(self) -> None:
        if self._kube_client is None:
            return
        self._kube_client.session.close()
        self._kube_client = None
