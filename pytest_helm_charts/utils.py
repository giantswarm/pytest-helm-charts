"""Different utilities required over the whole testing lib."""
import logging
import time
from typing import Dict, Any, List, TypeVar, Callable, Type, Optional, Iterable

import pykube.exceptions
from pykube import HTTPClient

from pytest_helm_charts.clusters import Cluster
from pytest_helm_charts.errors import WaitTimeoutError

DEFAULT_DELETE_TIMEOUT_SEC = 120

YamlDict = Dict[str, Any]

logger = logging.getLogger(__name__)

TNS = TypeVar("TNS", bound=pykube.objects.NamespacedAPIObject)
T = TypeVar("T", bound=pykube.objects.APIObject)
FactoryFunc = Callable[..., T]
MetaFactoryFunc = Callable[[pykube.HTTPClient, list[T]], FactoryFunc]


def wait_for_namespaced_objects_condition(
    kube_client: HTTPClient,
    obj_type: Type[TNS],
    obj_names: List[str],
    objs_namespace: str,
    obj_condition_func: Callable[[TNS], bool],
    timeout_sec: int,
    missing_ok: bool,
) -> List[TNS]:
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
    matching_objs: List[TNS] = []
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


def delete_and_wait_for_objects(
    kube_client: HTTPClient,
    obj_type: Type[T],
    objects_to_del: Iterable[T],
    timeout_sec: int = DEFAULT_DELETE_TIMEOUT_SEC,
) -> None:
    for kube_object in objects_to_del:
        kube_object.delete()

    any_exists = True
    times = 0
    while any_exists:
        if times >= timeout_sec:
            raise WaitTimeoutError(f"timeout of {timeout_sec} s crossed while waiting for objects to be deleted")
        any_exists = False
        for o in objects_to_del:
            objects_method = getattr(obj_type, "objects")
            objects_res = (
                objects_method(kube_client, namespace=o.namespace)
                if "namespace" in o.metadata
                else objects_method(kube_client)
            )
            if objects_res.get_or_none(name=o.name):
                any_exists = True
                time.sleep(1)
                times += 1
                break


def object_factory_helper(
    kube_cluster: Cluster, meta_func: MetaFactoryFunc, obj_type: Type[T], timeout_sec: int = DEFAULT_DELETE_TIMEOUT_SEC
) -> Iterable[FactoryFunc]:
    created_objects: list[T] = []

    yield meta_func(kube_cluster.kube_client, created_objects)

    delete_and_wait_for_objects(kube_cluster.kube_client, obj_type, created_objects, timeout_sec)
