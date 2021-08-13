from typing import List, Optional

import pykube
import yaml
from pykube import HTTPClient, ConfigMap

from pytest_helm_charts.giantswarm_app_platform.custom_resources import AppCR
from pytest_helm_charts.giantswarm_app_platform.entities import ConfiguredApp
from pytest_helm_charts.utils import wait_for_namespaced_objects_condition, YamlDict


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
    """
    Block until all the apps are running or timeout is reached.

    Args:
        kube_client: client to use to connect to the k8s cluster
        app_names: a list of application names to check; all of the applications must be running for this
        function to succeed
        app_namespace: namespace where the App CRs of all the apps are stored
        timeout_sec: timeout for the call
        missing_ok: when `True`, the function ignores that some of the apps listed in the `app_names`
        don't exist in k8s API and waits for them to show up; when `False`, an
        [ObjectNotFound](pykube.exceptions.ObjectDoesNotExist) exception is raised.

    Returns:
        The list of App CRs with all the apps listed in `app_names` included.

    Raises:
        TimeoutError: when timeout is reached.
        pykube.exceptions.ObjectDoesNotExist: when `missing_ok == False` and one of the apps
        listed in `app_names` can't be found in k8s API

    """
    apps = wait_for_namespaced_objects_condition(
        kube_client, AppCR, app_names, app_namespace, _app_deployed, timeout_sec, missing_ok
    )
    return apps


def wait_for_app_to_be_deleted(
    kube_client: HTTPClient,
    app_name: str,
    app_namespace: str,
    timeout_sec: int,
) -> bool:
    """
    Block until an App CR has status `deleted` or doesn't exist in k8s API.

    Args:
        kube_client: client to use to connect to the k8s cluster
        app_name: an application name to check
        app_namespace: namespace where all the App CRs are stored
        timeout_sec: timeout for the call

    Returns:
        `True` when the App CR was found with status `deleted` or was not found at all. `False` otherwise.

    Raises:
        TimeoutError: when timeout is reached.

    """
    try:
        apps = wait_for_namespaced_objects_condition(
            kube_client, AppCR, [app_name], app_namespace, _app_deleted, timeout_sec, missing_ok=False
        )
    except pykube.exceptions.ObjectDoesNotExist:
        return True
    return len(apps) == 1


def delete_app(configured_app: ConfiguredApp) -> None:
    """
    Deletes the app created by [create_app](create_app).
    Args:
        configured_app: ConfiguredApp (with optional ConfigMap configuration) to be deleted.

    Returns:
        None
    """
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
    """Creates and deploys a new app using App CR. Optionally creates a values ConfigMap. Calls are blocking.

    Args:
        kube_client: client to use to connect to the k8s cluster
        app_name: name of the app in the app catalog
        app_version: version of the app to use from the app catalog
        catalog_name: a name of the catalog used for the
        [AppCatalogCR](pytest_helm_charts.giantswarm_app_platform.custom_resources.AppCatalogCR);
        must already exist
        namespace: namespace where the App CR will be created
        deployment_namespace: namespace where the app will be deployed (can be different than `namespace`)
        config_values: any values that should be used to configure the app (same as `values.yaml` used for
        a Helm Chart directly).
        namespace_config_annotations: a dictionary of annotations that need to be added to the
        `deployment_namespace` created for the app
        namespace_config_labels: a dictionary of labels that need to be added to the `deployment_namespace`
        created for the app

    Returns:
        The [ConfiguredApp](.entities.ConfiguredApp) object that includes both AppCR and ConfigMap created to
        deploy the app.
    """
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
