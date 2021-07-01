"""This module introduces classes for handling different clusters."""
import json
import random
import socket
import subprocess
import time

from abc import ABC, abstractmethod
from typing import Optional, Generator
from contextlib import contextmanager, closing

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


    # From https://codeberg.org/hjacobs/pytest-kind/src/branch/main/pytest_kind/cluster.py#L134-L142
    def exec_kubectl(self, *args: str, **kwargs) -> str:
        """Run a kubectl command against the cluster and return the output as string."""
        return subprocess.check_output(
            ["kubectl", *args],
            env={"KUBECONFIG": str(self.kube_config_path)},
            encoding="utf-8",
            **kwargs,
        )


    def kubectl(self, subcmd_string: str, input="", output="json", **kwargs):
        """Run a kubectl command against the cluster and return the output"""
        subcmds = subcmd_string.split(" ")

        if input:
            kwargs["filename"] = "-"
        if output:
            kwargs["output"] = output
        if self.kube_config_path:
            kwargs["kubeconfig"] = self.kube_config_path
        if subcmds[0].lower() == "delete":
            del kwargs["output"]

        options = {f"--{option}={value}" for option, value in kwargs.items()}

        result = subprocess.check_output([
                "kubectl",
                *subcmds,
                *options
            ],
            encoding="utf-8",
            input=input
        )

        # return result from kubectl command
        # as parsed json if requested
        # as list if result is a list
        # as plain text otherwise

        if output == "json":
            output_json = json.loads(result)
            if "items" in output_json:
                return output_json["items"]
            return json.loads(result)
        return result


    # From https://codeberg.org/hjacobs/pytest-kind/src/branch/main/pytest_kind/cluster.py#L144-L193
    @contextmanager
    def port_forward(
        self,
        service_or_pod_name: str,
        remote_port: int,
        local_port: int = None,
        retries: int = 10,
        **kwargs
    ) -> Generator[int, None, None]:
        """Run "kubectl port-forward" for the given service/pod and use a random local port."""
        port_to_use: int
        proc = None

        if self.kube_config_path:
            kwargs["kubeconfig"] = self.kube_config_path

        options = {f"--{option}={value}" for option, value in kwargs.items()}

        for i in range(retries):
            if proc:
                proc.kill()
            # Linux epheremal port range starts at 32k
            port_to_use = local_port or random.randrange(5000, 30000)
            proc = subprocess.Popen(
                [
                    "kubectl",
                    "port-forward",
                    *options,
                    service_or_pod_name,
                    f"{port_to_use}:{remote_port}",
                ]
            )
            time.sleep(1)
            returncode = proc.poll()
            if returncode is not None:
                if i >= retries - 1:
                    raise Exception(
                        f"kubectl port-forward returned exit code {returncode}"
                    )
                else:
                    # try again
                    continue
            s = socket.socket()
            try:
                s.connect(("127.0.0.1", port_to_use))
            except:
                if i >= retries - 1:
                    raise
            finally:
                s.close()
        try:
            yield port_to_use
        finally:
            if proc:
                proc.kill()
