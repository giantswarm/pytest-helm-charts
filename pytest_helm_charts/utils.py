"""Different utilities required over the whole testing lib."""
import logging
import time
from typing import Dict, Any, List, TypeVar, Callable, Type, Optional

import pykube.exceptions
from pykube import HTTPClient, Deployment

YamlDict = Dict[str, Any]

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=pykube.objects.NamespacedAPIObject)


def wait_for_namespaced_objects_condition(
    kube_client: HTTPClient,
    obj_type: Type[T],
    obj_names: List[str],
    objs_namespace: str,
    obj_condition_func: Callable[[T], bool],
    timeout_sec: int,
    missing_ok: bool,
) -> List[T]:
    """
    Block until all the namespaced kubernetes objects of type `obj_type` pass `obj_condition_fun` or timeout is reached.

    Args:
        kube_client: client to use to connect to the k8s cluster
        obj_type: type of the objects to check; they most be derived from
            [NamespacedAPIObject](pykube.objects.NamespacedAPIObject)
        obj_names: a list of object resource names to check; all of the objects must be pass `obj_condition_fun`
            for this function to succeed
        objs_namespace: namespace where all the resources are created (single namespace for all resources)
        timeout_sec: timeout for the call
        obj_condition_func: a function that gets one instance of the resource object of type `obj_type`
            and returns boolean showing whether the object meets the condition or not. The call succeeds
            only if this `obj_condition_fun` returns `True` for every object passed in `obj_names`.
        missing_ok: when `True`, the function ignores that some of the objects listed in the `obj_names`
            don't exist in k8s API and waits for them to show up; when `False`, an
            [ObjectNotFound](pykube.exceptions.ObjectDoesNotExist) exception is raised.

    Returns:
        The list of namespaced object resources with all the objects listed in `obj_names` included.

    Raises:
        TimeoutError: when timeout is reached.
        pykube.exceptions.ObjectDoesNotExist: when `missing_ok == False` and one of the objects
            listed in `obj_names` can't be found in k8s API

    """
    if len(obj_names) == 0:
        raise ValueError("'obj_names' list can't be empty.")

    retries = 0
    all_ready = False
    matching_objs: List[T] = []
    while retries < timeout_sec:
        response = obj_type.objects(kube_client).filter(namespace=objs_namespace)
        retries += 1
        matching_objs = []
        for name in obj_names:
            try:
                obj = response.get_by_name(name)
                matching_objs.append(obj)
            except pykube.exceptions.ObjectDoesNotExist:
                if missing_ok:
                    pass
                else:
                    raise
        all_ready = len(matching_objs) == len(obj_names) and all(obj_condition_func(obj) for obj in matching_objs)
        if all_ready:
            break
        time.sleep(1)

    if not all_ready:
        raise TimeoutError(f"Error waiting for object of type {obj_type} to match the condition.")

    return matching_objs


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
            don't exist in k8s API and waits for them to show up; when `False`, an
            [ObjectNotFound](pykube.exceptions.ObjectDoesNotExist) exception is raised.

    Returns:
        The list of Deployment resources with all the objects listed in `deployment_names` included.

    Raises:
        TimeoutError: when timeout is reached.
        pykube.exceptions.ObjectDoesNotExist: when `missing_ok == False` and one of the objects
            listed in `deployment_names` can't be found in k8s API

    """
    result = wait_for_namespaced_objects_condition(
        kube_client,
        Deployment,
        deployment_names,
        deployments_namespace,
        _deployment_running,
        timeout_sec,
        missing_ok,
    )
    return result


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
    result = wait_for_namespaced_objects_condition(
        kube_client,
        pykube.StatefulSet,
        stateful_set_names,
        stateful_sets_namespace,
        _stateful_set_ready,
        timeout_sec,
        missing_ok=missing_ok,
    )
    return result


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
    result = wait_for_namespaced_objects_condition(
        kube_client,
        pykube.DaemonSet,
        daemon_set_names,
        daemon_sets_namespace,
        _daemon_set_ready,
        timeout_sec,
        missing_ok=missing_ok,
    )
    return result


def inject_extra(
    cr_dict: YamlDict,
    extra_metadata: Optional[YamlDict] = None,
    extra_spec: Optional[YamlDict] = None,
) -> YamlDict:
    if extra_metadata:
        cr_dict["metadata"].update(extra_metadata)
    if extra_spec:
        cr_dict["spec"].update(extra_spec)
    return cr_dict


def make_namespace_object(
    kube_client: pykube.HTTPClient,
    namespace_name: str,
    extra_metadata: Optional[dict] = None,
    extra_spec: Optional[dict] = None,
) -> pykube.Namespace:
    obj = inject_extra(
        {
            "apiVersion": "v1",
            "kind": "Namespace",
            "metadata": {
                "name": namespace_name,
            },
        },
        extra_metadata,
        extra_spec,
    )
    return pykube.Namespace(kube_client, obj)


def ensure_namespace_exists(
    kube_client: pykube.HTTPClient,
    namespace_name: str,
    extra_metadata: Optional[dict] = None,
    extra_spec: Optional[dict] = None,
) -> pykube.Namespace:
    """
    Checks if the Namespace exists and creates it if it doesn't
    Args:
        kube_client: client to use to connect to the k8s cluster
        namespace_name: a name of the Namespace to ensure
        extra_metadata: optional dict that will be merged with the 'metadata:' section of the object
        extra_spec: optional dict that will be merged with the 'spec:' section of the object

    Returns:
        Namespace resource object

    """
    ns = pykube.Namespace.objects(kube_client).get_or_none(name=namespace_name)
    if ns is None:
        ns = make_namespace_object(kube_client, namespace_name, extra_metadata, extra_spec)
        ns.create()
    return ns
