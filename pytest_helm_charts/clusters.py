"""This module introduces classes for handling different clusters."""
import json
import logging
import shutil
import subprocess  # nosec
from abc import ABC, abstractmethod
from typing import Optional, Any

from pykube import HTTPClient, KubeConfig

logger = logging.getLogger(__name__)


class Cluster(ABC):
    """Represents an abstract cluster."""

    _kube_client: Optional[HTTPClient]
    kube_config_path: Optional[str]

    def __init__(self, kube_config_path: Optional[str] = None):
        super().__init__()
        self._kube_client = None
        self.kube_config_path = kube_config_path

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

    def kubectl(  # noqa: C901
        self, subcmd_string: str, std_input: str = "", output_format: str = "json", **kwargs: str
    ) -> Any:
        """If your cluster delivers the kube.config file, run a kubectl command against the cluster
        and return the output. Otherwise, exception is raised."""
        if not self.kube_config_path:
            raise ValueError("'kube_config_path' can't be empty to use 'kubectl'")
        bin_name = "kubectl"
        if shutil.which(bin_name) is None:
            raise ValueError(f"Can't find {bin_name} executable. Please make sure it's available in $PATH.")

        subcmds = subcmd_string.split(" ")
        if len(subcmds) == 0:
            raise ValueError("You need to give at least one kubectl subcommand in the subcmd_string argument.")

        kwargs["kubeconfig"] = self.kube_config_path
        if std_input:
            kwargs["filename"] = "-"
        if output_format:
            kwargs["output"] = output_format
        if subcmds[0].lower() == "delete" and "output" in kwargs:
            del kwargs["output"]

        options = {f"--{option}={value}" for option, value in kwargs.items()}

        try:
            result = subprocess.check_output([bin_name, *subcmds, *options], encoding="utf-8", input=std_input)  # nosec
        except subprocess.CalledProcessError as e:
            logger.error(
                f"'kubectl' call returned an error. Exit code: '{e.returncode}', stdout: '{e.stdout}',"
                f"stderr: '{e.stderr}'"
            )
            raise

        # return result from kubectl command:
        # - as parsed json by default, extracting objects list to list
        # - as plain text otherwise

        if output_format == "json":
            output_json = json.loads(result)
            if "items" in output_json:
                return output_json["items"]
            return output_json
        return result


class ExistingCluster(Cluster):
    """Implementation of [Cluster](Cluster) that uses kube.config file to connect to external
    existing cluster.
    """

    def __init__(self, kube_config_path: str) -> None:
        super().__init__(kube_config_path)

    def create(self) -> HTTPClient:
        kube_config = KubeConfig.from_file(self.kube_config_path)
        self._kube_client = HTTPClient(kube_config)
        return self._kube_client

    def destroy(self) -> None:
        if self._kube_client is None:
            return
        self._kube_client.session.close()
        self._kube_client = None
