from typing import List

import pykube
from pykube import HTTPClient

from pytest_helm_charts.utils import wait_for_objects_condition


def _daemon_set_ready(ds: pykube.DaemonSet) -> bool:
    complete = (
        "desiredNumberScheduled" in ds.obj["status"]
        and "numberReady" in ds.obj["status"]
        and int(ds.obj["status"]["desiredNumberScheduled"]) == int(ds.obj["status"]["numberReady"])
    )
    return complete


def wait_for_daemon_sets_to_run(
    kube_client: HTTPClient,
    daemon_set_names: List[str],
    daemon_sets_namespace: str,
    timeout_sec: int,
    missing_ok: bool = False,
) -> List[pykube.DaemonSet]:
    """
    Block until all the DaemonSets are running or timeout is reached.

    Args:
        kube_client: client to use to connect to the k8s cluster
        daemon_set_names: a list of DaemonSet names to check
        daemon_sets_namespace: namespace where all the DaemonSets are created (single namespace for all resources)
        timeout_sec: timeout for the call
        missing_ok: when `True`, the function ignores that some of the objects listed in the `daemon_set_names`
            don't exist in k8s API and waits for them to show up; when `False`, an
            [ObjectNotFound](pykube.exceptions.ObjectDoesNotExist) exception is raised.

    Returns:
        The list of DaemonSet resources with all the objects listed in `daemon_set_names` included.

    Raises:
        TimeoutError: when timeout is reached.
        pykube.exceptions.ObjectDoesNotExist: when `missing_ok == False` and one of the objects
            listed in `daemon_set_names` can't be found in k8s API

    """
    result = wait_for_objects_condition(
        kube_client,
        pykube.DaemonSet,
        daemon_set_names,
        daemon_sets_namespace,
        _daemon_set_ready,
        timeout_sec,
        missing_ok=missing_ok,
    )
    return result
