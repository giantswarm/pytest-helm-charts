from typing import List

from pykube import Deployment, HTTPClient

from pytest_helm_charts.utils import wait_for_objects_condition


def _deployment_running(deploy: Deployment) -> bool:
    complete = (
        "status" in deploy.obj
        and "availableReplicas" in deploy.obj["status"]
        and "observedGeneration" in deploy.obj["status"]
        and "updatedReplicas" in deploy.obj["status"]
        and int(deploy.obj["status"]["observedGeneration"]) >= int(deploy.obj["metadata"]["generation"])
        and deploy.replicas == int(deploy.obj["status"]["updatedReplicas"])
        and deploy.replicas == int(deploy.obj["status"]["availableReplicas"])
    )
    return complete


def wait_for_deployments_to_run(
    kube_client: HTTPClient,
    deployment_names: List[str],
    deployments_namespace: str,
    timeout_sec: int,
    missing_ok: bool = True,
) -> List[Deployment]:
    """
    Block until all the Deployments are running or timeout is reached.

    Args:
        kube_client: client to use to connect to the k8s cluster
        deployment_names: a list of Deployment names to check
        deployments_namespace: namespace where all the Deployments are created (single namespace for all resources)
        timeout_sec: timeout for the call
        missing_ok: when `True`, the function ignores that some of the objects listed in the `deployment_names`
            don't exist in k8s API and waits for them to show up; when `False`, a
            `pykube.exceptions.ObjectDoesNotExist` exception is raised.

    Returns:
        The list of Deployment resources with all the objects listed in `deployment_names` included.

    Raises:
        TimeoutError: when timeout is reached.
        pykube.exceptions.ObjectDoesNotExist: when `missing_ok == False` and one of the objects
            listed in `deployment_names` can't be found in k8s API

    """
    result = wait_for_objects_condition(
        kube_client,
        Deployment,
        deployment_names,
        deployments_namespace,
        _deployment_running,
        timeout_sec,
        missing_ok,
    )
    return result
