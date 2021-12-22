from typing import List

import pykube
from pykube import HTTPClient

from pytest_helm_charts.utils import wait_for_objects_condition


def _stateful_set_ready(sts: pykube.StatefulSet) -> bool:
    complete = "readyReplicas" in sts.obj["status"] and sts.replicas == int(sts.obj["status"]["readyReplicas"])
    return complete


def wait_for_stateful_sets_to_run(
    kube_client: HTTPClient,
    stateful_set_names: List[str],
    stateful_sets_namespace: str,
    timeout_sec: int,
    missing_ok: bool = False,
) -> List[pykube.StatefulSet]:
    """
    Block until all the StatefulSets are running or timeout is reached.

    Args:
        kube_client: client to use to connect to the k8s cluster
        stateful_set_names: a list of StatefulSet names to check
        stateful_sets_namespace: namespace where all the StatefulSets are created (single namespace for all resources)
        timeout_sec: timeout for the call
        missing_ok: when `True`, the function ignores that some of the objects listed in the `stateful_set_names`
            don't exist in k8s API and waits for them to show up; when `False`, an
            [ObjectNotFound](pykube.exceptions.ObjectDoesNotExist) exception is raised.

    Returns:
        The list of StatefulSet resources with all the objects listed in `stateful_set_names` included.

    Raises:
        TimeoutError: when timeout is reached.
        pykube.exceptions.ObjectDoesNotExist: when `missing_ok == False` and one of the objects
            listed in `stateful_set_names` can't be found in k8s API

    """
    result = wait_for_objects_condition(
        kube_client,
        pykube.StatefulSet,
        stateful_set_names,
        stateful_sets_namespace,
        _stateful_set_ready,
        timeout_sec,
        missing_ok=missing_ok,
    )
    return result
