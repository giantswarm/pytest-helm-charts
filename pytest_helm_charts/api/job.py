from typing import List, Optional

import pykube
from pykube import Job, HTTPClient

from pytest_helm_charts.utils import wait_for_objects_condition, inject_extra


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
    """
    Block until all the Jobs are complete or timeout is reached.

    Args:
        kube_client: client to use to connect to the k8s cluster
        job_names: a list of Job names to check
        jobs_namespace: namespace where all the Jobs are created (single namespace for all resources)
        timeout_sec: timeout for the call
        missing_ok: when `True`, the function ignores that some of the objects listed in the `job_names`
            don't exist in k8s API and waits for them to show up; when `False`, an
            [ObjectNotFound](pykube.exceptions.ObjectDoesNotExist) exception is raised.

    Returns:
        The list of Job resources with all the objects listed in `job_names` included.

    Raises:
        TimeoutError: when timeout is reached.
        pykube.exceptions.ObjectDoesNotExist: when `missing_ok == False` and one of the objects
            listed in `job_names` can't be found in k8s API

    """
    result = wait_for_objects_condition(
        kube_client, Job, job_names, jobs_namespace, _job_complete, timeout_sec, missing_ok
    )
    return result


def make_job_object(
    kube_client: pykube.HTTPClient,
    name_prefix: str,
    namespace: str,
    command: List[str],
    image: str = "quay.io/giantswarm/busybox:1.32.0",
    restart_policy: str = "OnFailure",
    backoff_limit: int = 6,  # 6 is the default from k8s
    extra_metadata: Optional[dict] = None,
    extra_spec: Optional[dict] = None,
) -> pykube.Job:
    """
    Creates a Job object according to the parameters.

    Args:
        kube_client: client to use to connect to the k8s cluster
        name_prefix: `metadata.generateName` Job's object property that is used to name Pods
        namespace: Namespace to create the Job in
        command: command to run inside the Job pod
        image: container image to use
        restart_policy: Job's restart policy (as in k8s API)
        backoff_limit: Job's backoff limit (as in k8s API)
        extra_metadata: optional dict that will be merged with the 'metadata:' section of the object
        extra_spec: optional dict that will be merged with the 'spec:' section of the object

    Returns:
        Job object. The Job is not sent for creation to API server.
    """
    obj = inject_extra(
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
        extra_metadata,
        extra_spec,
    )
    return pykube.Job(kube_client, obj)


def create_job_and_run_to_completion(
    kube_client: pykube.HTTPClient,
    namespace: str,
    job: pykube.Job,
    timeout_sec: int = 60,
    missing_ok: bool = False,
) -> pykube.Job:
    """
    Creates Job object in k8s and blocks until it is completed.

    Args:
        kube_client: client to use to connect to the k8s cluster
        namespace: Namespace to create the Job in
        job: Job object to run and check.
        timeout_sec: timeout for the call
        missing_ok: when `True`, the function ignores that the Job doesn't yet exist in k8s API
            and waits for it to show up;
            when `False`, an [ObjectNotFound](pykube.exceptions.ObjectDoesNotExist) exception is raised.

    Returns:
        The Job object with refreshed state.

    Raises:
        TimeoutError: when timeout is reached.
        pykube.exceptions.ObjectDoesNotExist: when `missing_ok == False` and the `job` can't be found in k8s API

    """
    job.create()

    wait_for_jobs_to_complete(
        kube_client,
        [job.name],
        namespace,
        timeout_sec,
        missing_ok=missing_ok,
    )

    return job
