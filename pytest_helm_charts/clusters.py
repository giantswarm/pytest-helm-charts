"""This module introduces classes for handling different clusters."""
from abc import ABC, abstractmethod
from typing import Optional

from pykube import HTTPClient, KubeConfig


class Cluster(ABC):
    """Represents an abstract cluster."""

    @abstractmethod
    def create(self) -> HTTPClient:
        """Creates an instance of a cluster and returns HTTPClient to connect to it."""
        raise NotImplementedError

    @abstractmethod
    def destroy(self) -> None:
        """Destroys the cluster created earlier with a call to [create](Cluster.create)."""
        raise NotImplementedError

    @staticmethod
    def create_http_client_from_kube_config(kube_config: KubeConfig) -> HTTPClient:
        """Method for creating KubeConfig instances. Useful for mocking the HTTPClient"""
        return HTTPClient(kube_config)


class ExistingCluster(Cluster):
    """Implementation of [Cluster](Cluster) that uses kube.config
    for an existing cluster.
    """
    kube_client: Optional[HTTPClient]

    def __init__(self, kube_config: str) -> None:
        self.kube_config = kube_config

    def create(self) -> HTTPClient:
        kube_config = KubeConfig.from_file(self.kube_config)
        self.kube_client = self.create_http_client_from_kube_config(kube_config)
        return self.kube_client

    def destroy(self) -> None:
        if self.kube_client is None:
            return
        self.kube_client.session.close()
        self.kube_client = None
