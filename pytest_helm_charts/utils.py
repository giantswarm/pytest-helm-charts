"""Different utilities required over the whole testing lib."""
import logging
import time
from typing import Dict, Any, List, TypeVar, Callable, Type

import pykube.exceptions
from pykube import HTTPClient, Job, Service, Deployment

# YamlValue = Union[int, float, str, bool, List['YamlValue'], 'YamlDict']
from requests import Response

YamlDict = Dict[str, Any]

logger = logging.getLogger(__name__)

# TODO: doesn't work as T for method below
T = TypeVar("T", bound=pykube.objects.NamespacedAPIObject)


def wait_for_namespaced_objects_condition(
    kube_client: HTTPClient,
    obj_type: Type[T],
    obj_names: List[str],
    objs_namespace: str,
    obj_condition_fun: Callable[[T], bool],
    timeout_sec: int,
    missing_ok: bool,
) -> List[T]:
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
                assert obj is not None
                matching_objs.append(obj)
            except pykube.exceptions.ObjectDoesNotExist:
                if missing_ok:
                    pass
                else:
                    raise
        all_ready = len(matching_objs) == len(obj_names) and all(obj_condition_fun(obj) for obj in matching_objs)
        if all_ready:
            break
        time.sleep(1)

    if not all_ready:
        raise TimeoutError(f"Error waiting for object of type {obj_type} to match the condition.")

    return matching_objs


def _job_complete(job: Job) -> bool:
    complete = (
        "status" in job.obj
        and "conditions" in job.obj["status"]
        and len(job.obj["status"]["conditions"]) > 0
        and job.obj["status"]["conditions"][0]["type"] == "Complete"
    )
    return complete


def wait_for_jobs_to_complete(
    kube_client: HTTPClient, job_names: List[str], jobs_namespace: str, timeout_sec: int, missing_ok: bool = True
) -> List[Job]:
    result = wait_for_namespaced_objects_condition(
        kube_client, Job, job_names, jobs_namespace, _job_complete, timeout_sec, missing_ok
    )
    return result


def _deployment_running(d: Deployment) -> bool:
    complete = (
        d.ready and "availableReplicas" in d.obj["status"] and d.replicas == int(d.obj["status"]["availableReplicas"])
    )
    return complete


def wait_for_deployments_to_run(
    kube_client: HTTPClient,
    deployment_names: List[str],
    deployments_namespace: str,
    timeout_sec: int,
    missing_ok: bool = True,
) -> List[Deployment]:
    result = wait_for_namespaced_objects_condition(
        kube_client, Deployment, deployment_names, deployments_namespace, _deployment_running, timeout_sec, missing_ok,
    )
    return result


def proxy_http_request(client: HTTPClient, srv: Service, method, path, **kwargs) -> Response:
    """Template request to proxy of a Service.
    Args:
        :param client: HTTPClient to use.
        :param srv: Service you want to proxy.
        :param method: The http request method e.g. 'GET', 'POST' etc.
        :param path: The URI path for the request.
        :param kwargs: Keyword arguments for the proxy_http_get function.
    Returns:
        The Response data.
    """
    if "port" in kwargs:
        port = kwargs["port"]
    else:
        port = srv.obj["spec"]["ports"][0]["port"]
    kwargs["url"] = f"services/{srv.name}:{port}/proxy/{path}"
    kwargs["namespace"] = srv.namespace
    kwargs["version"] = srv.version
    return client.request(method, **kwargs)


def proxy_http_get(client: HTTPClient, srv: Service, path: str, **kwargs) -> Response:
    """Issue a GET request to proxy of a Service.
    Args:
        :param client: HTTPClient to use.
        :param srv: Service you want to proxy.
        :param path: The URI path for the request.
        :param kwargs: Keyword arguments for the proxy_http_get function.
    Returns:
        The response data.
    """
    return proxy_http_request(client, srv, "GET", path, **kwargs)


def proxy_http_post(client: HTTPClient, srv: Service, path: str, **kwargs) -> Response:
    """Issue a POST request to proxy of a Service.
    Args:
        :param client: HTTPClient to use.
        :param srv: Service you want to proxy.
        :param path: The URI path for the request.
        :param kwargs: Keyword arguments for the proxy_http_get function.
    Returns:
        The response data.
    """
    return proxy_http_request(client, srv, "POST", path, **kwargs)


def proxy_http_put(client: HTTPClient, srv: Service, path: str, **kwargs) -> Response:
    """Issue a PUT request to proxy of a Service.
    Args:
        :param client: HTTPClient to use.
        :param srv: Service you want to proxy.
        :param path: The URI path for the request.
        :param kwargs: Keyword arguments for the proxy_http_get function.
    Returns:
        The response data.
    """
    return proxy_http_request(client, srv, "PUT", path, **kwargs)


def proxy_http_delete(client: HTTPClient, srv: Service, path: str, **kwargs) -> Response:
    """Issue a DELETE request to proxy of a Service.
    Args:
        :param client: HTTPClient to use.
        :param srv: Service you want to proxy.
        :param path: The URI path for the request.
        :param kwargs: Keyword arguments for the proxy_http_get function.
    Returns:
        The response data.
    """
    return proxy_http_request(client, srv, "DELETE", path, **kwargs)
