from typing import List, Optional

import pykube
import yaml
from pykube import HTTPClient, ConfigMap

from .custom_resources import AppCR
from .entities import ConfiguredApp
from ..utils import wait_for_namespaced_objects_condition, YamlDict


def _app_has_status(app: AppCR, status: str) -> bool:
    complete = (
        "status" in app.obj
        and "release" in app.obj["status"]
        and "appVersion" in app.obj["status"]
        and "status" in app.obj["status"]["release"]
        and app.obj["status"]["release"]["status"].lower() == status
    )
    return complete


def _app_deployed(app: AppCR) -> bool:
    return _app_has_status(app, "deployed")


def _app_deleted(app: AppCR) -> bool:
    return _app_has_status(app, "deleted")


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


def wait_for_app_to_be_deleted(
    kube_client: HTTPClient,
    app_name: str,
    app_namespace: str,
    timeout_sec: int,
    missing_ok: bool = False,
) -> bool:
    try:
        apps = wait_for_namespaced_objects_condition(
            kube_client, AppCR, [app_name], app_namespace, _app_deleted, timeout_sec, missing_ok
        )
    except pykube.exceptions.ObjectDoesNotExist:
        return True
    return len(apps) == 1


def delete_app(configured_app: ConfiguredApp):
    configured_app.app.delete()
    if configured_app.app_cm:
        configured_app.app_cm.delete()
    # TODO: wait until finalizer is gone


def create_app(
    kube_client: HTTPClient,
    app_name: str,
    app_version: str,
    catalog_name,
    namespace: str,
    deployment_namespace: str,
    config_values: YamlDict = None,
    namespace_config_annotations: YamlDict = None,
    namespace_config_labels: YamlDict = None,
) -> ConfiguredApp:
    if config_values is None:
        config_values = {}
    if namespace_config_annotations is None:
        namespace_config_annotations = {}
    if namespace_config_labels is None:
        namespace_config_labels = {}

    # TODO: include proper regexp validation
    assert app_name != ""
    assert app_version != ""
    assert catalog_name != ""
    api_version = "application.giantswarm.io/v1alpha1"
    app_cm_name = "{}-testing-user-config".format(app_name)
    kind = "App"
    app: YamlDict = {
        "apiVersion": api_version,
        "kind": kind,
        "metadata": {
            "name": app_name,
            "namespace": namespace,
            "labels": {"app": app_name, "app-operator.giantswarm.io/version": "0.0.0"},
        },
        "spec": {
            "catalog": catalog_name,
            "version": app_version,
            "kubeConfig": {"inCluster": True},
            "name": app_name,
            "namespace": deployment_namespace,
            "namespaceConfig": {
                "annotations": namespace_config_annotations,
                "labels": namespace_config_labels,
            },
        },
    }
    app_cm_obj: Optional[ConfigMap] = None
    if config_values:
        app["spec"]["config"] = {"configMap": {"name": app_cm_name, "namespace": namespace}}
        app_cm: YamlDict = {
            "apiVersion": "v1",
            "kind": "ConfigMap",
            "metadata": {"name": app_cm_name, "namespace": namespace},
            "data": {"values": yaml.dump(config_values)},
        }
        app_cm_obj = ConfigMap(kube_client, app_cm)
        app_cm_obj.create()
    app_obj = AppCR(kube_client, app)
    app_obj.create()
    return ConfiguredApp(app_obj, app_cm_obj)
