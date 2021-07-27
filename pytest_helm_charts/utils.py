"""Different utilities required over the whole testing lib."""
import logging
import time
import requests
import json

from typing import Dict, Any, List, TypeVar, Callable, Type

import pykube.exceptions
from pykube import HTTPClient, Job, Deployment

# YamlValue = Union[int, float, str, bool, List['YamlValue'], 'YamlDict']

YamlDict = Dict[str, Any]

logger = logging.getLogger(__name__)

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


def _deployment_running(deploy: Deployment) -> bool:
    complete = (
        deploy.ready
        and "availableReplicas" in deploy.obj["status"]
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


def ensure_namespace_exists(kube_client: pykube.HTTPClient, namespace_name: str) -> pykube.Namespace:
    ns = pykube.Namespace.objects(kube_client).get_or_none(name=namespace_name)
    if ns is None:
        obj = {
            "apiVersion": "v1",
            "kind": "Namespace",
            "metadata": {
                "name": namespace_name,
            },
        }
        ns = pykube.Namespace(kube_client, obj)
        ns.create()
    return ns


def make_job_object(
    kube_client: pykube.HTTPClient,
    name_prefix: str,
    namespace: str,
    command: List[str],
    image: str = "quay.io/giantswarm/busybox:1.32.0",
    restart_policy: str = "OnFailure",
    backoff_limit: int = 6,  # 6 is the default from k8s
) -> pykube.Job:
    return pykube.Job(
        kube_client,
        {
            "apiVersion": "batch/v1",
            "kind": "Job",
            "metadata": {"generateName": name_prefix, "namespace": namespace},
            "spec": {
                "backoffLimit": backoff_limit,
                "template": {
                    "spec": {
                        "containers": [
                            {
                                "name": f"{name_prefix}job",
                                "image": image,
                                "command": command,
                            }
                        ],
                        "restartPolicy": restart_policy,
                    },
                },
            },
        },
    )


def create_job_and_run_to_completion(
    kube_client: pykube.HTTPClient,
    namespace: str,
    job: pykube.Job,
    timeout_sec: int = 60,
    missing_ok: bool = False,
) -> pykube.Job:
    job.create()

    wait_for_jobs_to_complete(
        kube_client,
        [job.name],
        namespace,
        timeout_sec,
        missing_ok=missing_ok,
    )

    return job


def forward_requests(kubernetes_cluster, namespace, forward_to, port, rel_url="", retries=3, **kwargs):
    method = "POST" if "json" in kwargs else "GET"

    while retries:
        try:
            with kubernetes_cluster.port_forward(forward_to, port, namespace=namespace, retries=1) as f_port:
                res = requests.request(method, f"http://localhost:{f_port}{rel_url}", **kwargs)
                res.raise_for_status()
                try:
                    return res.json()
                except json.decoder.JSONDecodeError:
                    return res.text

        # reraise if out of retries
        except OSError as e:
            logger.warning(f"ConnectionError: {repr(e)}")
            if e and retries == 0:
                raise e
        except Exception as e:
            logger.warning(repr(e))
            if e and retries == 0:
                raise e

        retries -= 1
        logger.info(f"retries left: {retries}")
