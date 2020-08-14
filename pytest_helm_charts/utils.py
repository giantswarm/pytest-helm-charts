"""Different utilities required over the whole testing lib."""
import concurrent.futures
import logging
from typing import Dict, Any, List, TypeVar, Callable, Type, Tuple

import pykube.exceptions
from pykube import HTTPClient, Job, Service, Deployment, Endpoint

# YamlValue = Union[int, float, str, bool, List['YamlValue'], 'YamlDict']
from requests import Response

YamlDict = Dict[str, Any]

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=pykube.objects.NamespacedAPIObject)


def _wait_for_namespaced_objects_condition(
    kube_client: HTTPClient,
    obj_type: Type[T],
    obj_names: List[str],
    objs_namespace: str,
    obj_condition_fun: Callable[[T], bool],
    matching_objs: Dict[str, T],
) -> None:
    watch = obj_type.objects(kube_client).filter(namespace=objs_namespace).watch()
    for event in watch:
        if event.object.name not in obj_names:
            continue
        matching_objs[event.object.name] = event.object
        all_ready = len(matching_objs) == len(obj_names) and all(
            obj_condition_fun(obj) for obj in matching_objs.values()
        )
        if all_ready:
            break


def wait_for_namespaced_objects_condition(
    kube_client: HTTPClient,
    obj_type: Type[T],
    obj_names: List[str],
    objs_namespace: str,
    obj_condition_fun: Callable[[T], bool],
    timeout_sec: int,
) -> Dict[str, T]:
    if len(obj_names) == 0:
        raise ValueError("'obj_names' list can't be empty.")

    matching_objs: Dict[str, T] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        status_future = executor.submit(
            _wait_for_namespaced_objects_condition,
            kube_client,
            obj_type,
            obj_names,
            objs_namespace,
            obj_condition_fun,
            matching_objs,
        )
        done, not_done = concurrent.futures.wait([status_future], timeout=timeout_sec)

        if len(not_done) > 0:
            status_future.cancel()
            raise TimeoutError(f"Error waiting for object of type {obj_type} to match the condition.")

    return matching_objs


def _job_complete(job: Job) -> bool:
    complete = (
        "status" in job.obj
        and isinstance(job.obj["status"], dict)
        and "conditions" in job.obj["status"]
        and len(job.obj["status"]["conditions"]) > 0
        and job.obj["status"]["conditions"][0]["type"] == "Complete"
    )
    return complete


def wait_for_jobs_to_complete(
    kube_client: HTTPClient, job_names: List[str], jobs_namespace: str, timeout_sec: int
) -> Dict[str, Job]:
    result = wait_for_namespaced_objects_condition(
        kube_client, Job, job_names, jobs_namespace, _job_complete, timeout_sec
    )
    return result


def _deployment_running(d: Deployment) -> bool:
    complete = (
        "status" in d.obj
        and isinstance(d.obj["status"], dict)
        and all(key in d.obj["status"] for key in ("observedGeneration", "updatedReplicas", "availableReplicas"))
        and d.ready
        and d.replicas == int(d.obj["status"]["availableReplicas"])
    )
    return complete


def wait_for_deployments_to_run(
    kube_client: HTTPClient, deployment_names: List[str], deployments_namespace: str, timeout_sec: int,
) -> Dict[str, Deployment]:
    result = wait_for_namespaced_objects_condition(
        kube_client, Deployment, deployment_names, deployments_namespace, _deployment_running, timeout_sec,
    )
    return result


def wait_for_services_to_have_all_endpoints(
    kube_client: HTTPClient,
    service_and_deployment_names: List[Tuple[str, str]],
    services_namespace: str,
    timeout_sec: int,
) -> Dict[str, Endpoint]:
    service_names = [x[0] for x in service_and_deployment_names]
    deployment_names = [x[1] for x in service_and_deployment_names]

    deployments = wait_for_deployments_to_run(kube_client, deployment_names, services_namespace, timeout_sec)

    def _services_have_endpoints(e: Endpoint) -> bool:
        complete = (
            "subsets" in e.obj
            and isinstance(e.obj["subsets"], list)
            and sum(len(s["addresses"]) for s in e.obj["subsets"])
            == deployments[e.name].obj["status"]["availableReplicas"]
        )
        return complete

    result = wait_for_namespaced_objects_condition(
        kube_client, Endpoint, service_names, services_namespace, _services_have_endpoints, timeout_sec,
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
