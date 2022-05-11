import logging
from copy import deepcopy
from typing import List, Protocol, Optional, NamedTuple

import pykube
import yaml
from pykube import HTTPClient, ConfigMap
from pykube.objects import NamespacedAPIObject

from pytest_helm_charts.k8s.fixtures import NamespaceFactoryFunc
from pytest_helm_charts.giantswarm_app_platform.catalog import CatalogFactoryFunc
from pytest_helm_charts.utils import YamlDict, wait_for_objects_condition, inject_extra


logger = logging.getLogger(__name__)


class AppCR(NamespacedAPIObject):
    version = "application.giantswarm.io/v1alpha1"
    endpoint = "apps"
    kind = "App"


class ConfiguredApp(NamedTuple):
    """Class that represents application deployed by App CR and its optional configuration in ConfigMap."""

    app: AppCR
    app_cm: Optional[ConfigMap]


class AppFactoryFunc(Protocol):
    def __call__(
        self,
        app_name: str,
        app_version: str,
        catalog_name: str,
        catalog_namespace: str,
        catalog_url: str,
        namespace: str = "default",
        deployment_namespace: str = "default",
        config_values: YamlDict = None,
        extra_metadata: Optional[dict] = None,
        extra_spec: Optional[dict] = None,
        timeout_sec: int = 60,
    ) -> ConfiguredApp:
        ...


def app_factory_func(
    kube_client: HTTPClient,
    catalog_factory: CatalogFactoryFunc,
    namespace_factory: NamespaceFactoryFunc,
    created_apps: List[ConfiguredApp],
) -> AppFactoryFunc:
    def _app_factory(
        app_name: str,
        app_version: str,
        catalog_name: str,
        catalog_namespace: str,
        catalog_url: str,
        namespace: str = "default",
        deployment_namespace: str = "default",
        config_values: YamlDict = None,
        extra_metadata: Optional[dict] = None,
        extra_spec: Optional[dict] = None,
        timeout_sec: int = 60,
    ) -> ConfiguredApp:
        """Factory function used to create and deploy new apps using App CR. Calls are blocking.

        Args:
             app_name: name of the app in the app catalog
             app_version: version of the app to use from the app catalog
             catalog_name: a name of the catalog used for the
                [CatalogCR](pytest_helm_charts.giantswarm_app_platform.catalog.CatalogCR);
                new catalog is created only when one with the same name doesn't already exist
             catalog_namespace: namespace where the catalog catalog_name is defined
             catalog_url: URL of the catalog to install the application from; this is used only if a catalog
                with the same name doesn't already exist (then a new catalog with the given name and URL is created
                in the k8s API)
             namespace: namespace where the App CR will be created
             deployment_namespace: namespace where the app will be deployed (can be different from `namespace`)
             config_values: any values that should be used to configure the app (same as `values.yaml` used for
                a Helm Chart directly).
             extra_metadata: optional dict that will be merged with the 'metadata:' section of the object
             extra_spec: optional dict that will be merged with the 'spec:' section of the object
             timeout_sec: timeout in seconds for the create operation

        Returns:
            The [ConfiguredApp](ConfiguredApp) object that includes both AppCR and ConfigMap created to
            deploy the app.

        Raises:
            pykube.exceptions.ObjectDoesNotExist: if for any reason the created App CR object doesn't exist after
                creation and it's impossible to check its readiness.
                TimeoutError: when the timeout has been reached.
        """
        assert catalog_url != ""
        catalog_factory(catalog_name, catalog_namespace, catalog_url)
        namespace_factory(namespace)
        configured_app = create_app(
            kube_client,
            app_name,
            app_version,
            catalog_name,
            catalog_namespace,
            namespace,
            deployment_namespace,
            config_values,
            extra_metadata,
            extra_spec,
        )
        created_apps.append(configured_app)
        logger.debug(f"Created App '{configured_app.app.namespace}/{configured_app.app.name}'.")
        if timeout_sec > 0:
            wait_for_apps_to_run(kube_client, [app_name], namespace, timeout_sec)

        # we return a new object here, so that user doesn't alter the one added to created_apps
        return deepcopy(configured_app)

    return _app_factory


def _app_has_status(app: AppCR, status: str) -> bool:
    complete = (
        "status" in app.obj
        and "release" in app.obj["status"]
        and "appVersion" in app.obj["status"]
        and "status" in app.obj["status"]["release"]
        and app.obj["status"]["release"]["status"].lower() == status
    )
    return complete


def _app_failed(app: AppCR) -> bool:
    return _app_has_status(app, "failed")


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
    fail_fast: bool = False,
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
        fail_fast: if set to True, the function fails as soon as the App reaches 'status=failed`, without
            waiting for any subsequent status changes.

    Returns:
        The list of App CRs with all the apps listed in `app_names` included.

    Raises:
        TimeoutError: when timeout is reached.
        pykube.exceptions.ObjectDoesNotExist: when `missing_ok == False` and one of the apps
            listed in `app_names` can't be found in k8s API
        ObjectStatusError: when App object has `Status: failed` status.

    """
    apps = wait_for_objects_condition(
        kube_client,
        AppCR,
        app_names,
        app_namespace,
        _app_deployed,
        timeout_sec,
        missing_ok,
        _app_failed if fail_fast else None,
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
        apps = wait_for_objects_condition(
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


def make_app_object(
    kube_client: HTTPClient,
    app_name: str,
    app_version: str,
    catalog_name: str,
    catalog_namespace: str,
    namespace: str,
    deployment_namespace: str,
    config_values: YamlDict = None,
    extra_metadata: Optional[dict] = None,
    extra_spec: Optional[dict] = None,
) -> ConfiguredApp:
    """Creates a new App object. Optionally creates a values ConfigMap. Objects are not sent to API server.

    Args:
        kube_client: client to use to connect to the k8s cluster
        app_name: name of the app in the app catalog
        app_version: version of the app to use from the app catalog
        catalog_name: a name of the catalog used for the
            [CatalogCR](pytest_helm_charts.giantswarm_app_platform.catalog.CatalogCR);
            must already exist
        catalog_namespace: a namespace of the
            [CatalogCR](pytest_helm_charts.giantswarm_app_platform.catalog.CatalogCR)
        namespace: namespace where the App CR will be created
        deployment_namespace: namespace where the app will be deployed (can be different than `namespace`)
        config_values: any values that should be used to configure the app (same as `values.yaml` used for
            a Helm Chart directly).
        extra_metadata: optional dict that will be merged with the 'metadata:' section of the object
        extra_spec: optional dict that will be merged with the 'spec:' section of the object

    Returns:
        The [ConfiguredApp](ConfiguredApp) object that includes both AppCR and ConfigMap.
    """
    if config_values is None:
        config_values = {}

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
            "catalogNamespace": catalog_namespace,
            "version": app_version,
            "kubeConfig": {"inCluster": True},
            "name": app_name,
            "namespace": deployment_namespace,
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
    app = inject_extra(app, extra_metadata, extra_spec)
    app_obj = AppCR(kube_client, app)
    return ConfiguredApp(app_obj, app_cm_obj)


def create_app(
    kube_client: HTTPClient,
    app_name: str,
    app_version: str,
    catalog_name: str,
    catalog_namespace: str,
    namespace: str,
    deployment_namespace: str,
    config_values: YamlDict = None,
    extra_metadata: Optional[dict] = None,
    extra_spec: Optional[dict] = None,
) -> ConfiguredApp:
    configured_app = make_app_object(
        kube_client,
        app_name,
        app_version,
        catalog_name,
        catalog_namespace,
        namespace,
        deployment_namespace,
        config_values,
        extra_metadata,
        extra_spec,
    )
    if configured_app.app_cm:
        configured_app.app_cm.create()
    configured_app.app.create()
    return configured_app
