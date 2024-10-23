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
        self,
        subcmd_string: str,
        std_input: str = "",
        output_format: str = "json",
        use_shell: bool = False,
        **kwargs: str,
    ) -> Any:
        """Execute command by running 'kubectl' binary.

        If your cluster delivers the kube.config file, run a kubectl command against the cluster
        and return the output. Otherwise, exception is raised.

        Args:
            subcmd_string (str): Command to run, like "delete pod abc"
            std_input (str): Use this to pass a manifest file directly as a string (results in 'kubectl [cmd] -f -')
            output_format (str): Option "--output" as passed to 'kubectl'. Default is 'json', make sure to change to ""
                for commands that don't return JSON.
            use_shell: Whether the 'kubectl' command should be invoked directly (when 'False') or wrapped in system
                shell ('True'). 'False' by default.
            kwargs: arbitrary dictionary of options and values that will be passed directly to 'kubectl'

        Returns:
            str: The output printed by 'kubectl', if the command succeeded (exit code was 0)

        Raises:
            subprocess.CalledProcessError: If the command exited with non-zero exit code
        """
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
        if subcmds[0].lower() in ["delete", "patch", "label", "annotate"] and "output" in kwargs:
            del kwargs["output"]

        options = {f"--{option}={value}" for option, value in sorted(kwargs.items())}

        try:
            cmd = (
                bin_name + " " + subcmd_string + " " + " ".join(options)
                if use_shell
                else [bin_name, *subcmds, *options]
            )
            result = subprocess.check_output(
                cmd, stderr=subprocess.PIPE, encoding="utf-8", input=std_input, shell=use_shell  # nosec
            )
        except subprocess.CalledProcessError as e:
            logger.error(
                f"'kubectl' call returned an error. Exit code: '{e.returncode}', stdout: '{e.stdout}',"
                f"stderr: '{e.stderr}'"
            )
            raise

        # return result from kubectl command:
        # - as parsed json by default, extracting objects list to list
        # - as plain text otherwise

        if "output" in kwargs and kwargs["output"] == "json":
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
