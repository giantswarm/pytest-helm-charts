"""Different utilities required over the whole testing lib."""
import logging
import time
from typing import Dict, Any

import pykube.exceptions
from pykube import HTTPClient, Job

# YamlValue = Union[int, float, str, bool, List['YamlValue'], 'YamlDict']

YamlDict = Dict[str, Any]

logger = logging.getLogger(__name__)


def wait_for_job(kube_client: HTTPClient, job_name: str, namespace: str, max_wait_time_sec: int):
    job: Job
    wait_time_sec = 0
    while True:
        try:
            job = Job.objects(kube_client).filter(namespace=namespace).get(name=job_name)
            status = job.obj["status"]
            if (
                status
                and "conditions" in status
                and len(status["conditions"])
                and status["conditions"][0]["type"] == "Complete"
            ):
                break
        except pykube.exceptions.ObjectDoesNotExist:
            pass
        if wait_time_sec >= max_wait_time_sec:
            raise TimeoutError(
                "Job {} in namespace {} was not completed in {} seconds".format(job_name, namespace, max_wait_time_sec)
            )
        logger.info("Waiting for gatling job to complete...")
        time.sleep(1)
        wait_time_sec += 1
    return job
