"""Different utilities required over the whole testing lib."""
import logging
import time
from typing import Dict, Any, List, TypeVar, Callable, Type, Optional, Iterable

import pykube.exceptions
from pykube import HTTPClient

from pytest_helm_charts.clusters import Cluster
from pytest_helm_charts.errors import WaitTimeoutError, ObjectStatusError

DEFAULT_DELETE_TIMEOUT_SEC = 120

YamlDict = Dict[str, Any]

logger = logging.getLogger(__name__)

TNS = TypeVar("TNS", bound=pykube.objects.NamespacedAPIObject)
T = TypeVar("T", bound=pykube.objects.APIObject)
FactoryFunc = Callable[..., T]
MetaFactoryFunc = Callable[[pykube.HTTPClient, List[T]], FactoryFunc]


def wait_for_objects_condition(  # noqa: C901
    kube_client: HTTPClient,
    obj_type: Type[T],
    obj_names: List[str],
    objs_namespace: Optional[str],
    obj_condition_func: Callable[[T], bool],
    timeout_sec: int,
    missing_ok: bool,
    failure_condition_func: Optional[Callable[[T], bool]] = None,
) -> List[T]:
    """
    Block until all the kubernetes objects of type `obj_type` pass `obj_condition_fun` or timeout is reached.
        If `objs_namespace` is None, objects are treated as cluster-scope, otherwise as namespace-scope. If
        optional `failure_condition_func` is passed, it is executed when objects are refreshed and if it evaluates to
        `True`, it throws `ObjectStatusError` exception.

    Args:
        kube_client: client to use to connect to the k8s cluster
        obj_type: type of the objects to check; they most be derived from
            [APIObject](pykube.objects.APIObject)
        obj_names: a list of object resource names to check; all the objects must pass `obj_condition_fun`
            for this function to end with success
        objs_namespace: namespace where all the resources should be present (single namespace for all resources).
            If 'None', then it is assumed objects passed are cluster-scope
        timeout_sec: timeout for the call
        obj_condition_func: a function that gets one instance of the resource object of type `obj_type`
            and returns boolean showing whether the object meets the condition or not. The call succeeds
            only if this `obj_condition_fun` returns `True` for every object passed in `obj_names`.
        missing_ok: when `True`, the function ignores that some objects listed in the `obj_names`
            don't exist in k8s API and waits for them to show up; when `False`, an
            [ObjectNotExist](pykube.exceptions.ObjectDoesNotExist) exception is raised.
        failure_condition_func: if not None, then each monitored object is passed to this function. If it
            returns `True`, the `ObjectStatusError` is raised.

    Returns:
        The list of object resources with all the objects listed in `obj_names` included in the list.

    Raises:
        TimeoutError: when timeout is reached.
        pykube.exceptions.ObjectDoesNotExist: when `missing_ok == False` and one of the objects
            listed in `obj_names` can't be found in k8s API
        ObjectStatusError: when `failure_condition_func` is not None and any of the objects in `obj_names`
            returned `True` from this function.

    """
    if len(obj_names) == 0:
        raise ValueError("'obj_names' list can't be empty.")

    retries = 0
    all_ready = False
    matching_objs: List[T] = []
    while retries < timeout_sec:
        response = obj_type.objects(kube_client)
        if objs_namespace:
            response = response.filter(namespace=objs_namespace)
        retries += 1
        matching_objs = []
        for name in obj_names:
            try:
                obj = response.get_by_name(name)
                failed = failure_condition_func and failure_condition_func(obj)
                if failed:
                    raise ObjectStatusError(
                        f"Object's '{obj.namespace}/{obj.name}' status shows failure when waiting "
                        f"for the object's condition to pass."
                    )
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
    """
    For each object in `objects_to_delete`, make an API call to delete it, then wait until the object is gone
    from k8s API server.

    Args:
        kube_client: client to use to connect to the k8s cluster
        obj_type: type of the objects to check; they should be derived from
            [APIObject](pykube.objects.APIObject)
        objects_to_del: iterable of [APIObject](pykube.objects.APIObject) to delete. All objects must be of the same
            specific type.
        timeout_sec: timeout for all the objects in the list to be gone from API server.

    Returns: None

    """
    for kube_object in objects_to_del:
        kube_object.delete()
        obj_name = f"{kube_object.namespace}/{kube_object.name}" if kube_object.namespace else kube_object.name
        logger.debug(f"Deleted object of kind '{obj_type}' named '{obj_name}'.")

    any_exists = True
    times = 0
    while any_exists:
        if times >= timeout_sec:
            raise WaitTimeoutError(f"timeout of {timeout_sec} s exceeded while waiting for objects to be deleted")
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
    kube_cluster: Cluster,
    meta_func: MetaFactoryFunc,
    obj_type: Type[T],
    timeout_sec: int = DEFAULT_DELETE_TIMEOUT_SEC,
) -> Iterable[FactoryFunc]:
    created_objects: List[T] = []

    yield meta_func(kube_cluster.kube_client, created_objects)

    delete_and_wait_for_objects(kube_cluster.kube_client, obj_type, created_objects, timeout_sec)
