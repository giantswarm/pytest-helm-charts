from typing import List

from pykube import HTTPClient

from pytest_helm_charts.giantswarm_app_platform.custom_resources import AppCR
from pytest_helm_charts.utils import wait_for_namespaced_objects_condition


def _app_deployed(app: AppCR) -> bool:
    complete = (
        "status" in app.obj
        and "release" in app.obj["status"]
        and "appVersion" in app.obj["status"]
        and "status" in app.obj["status"]["release"]
        and app.obj["status"]["release"]["status"] == "deployed"
    )
    return complete


def wait_for_apps_to_run(
    kube_client: HTTPClient,
    app_names: List[str],
    app_namespace: str,
    timeout_sec: int,
    missing_ok: bool = False,
) -> List[AppCR]:
    apps = wait_for_namespaced_objects_condition(
        kube_client, AppCR, app_names, app_namespace, _app_deployed, timeout_sec, missing_ok
    )
    return apps
