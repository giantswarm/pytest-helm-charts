from typing import Callable, List, NamedTuple, Optional

import yaml
from pykube import HTTPClient, ConfigMap

from .app_catalog import AppCatalogFactoryFunc
from .custom_resources import AppCR
from .utils import wait_for_apps_to_run
from ..fixtures import NamespaceFactoryFunc
from ..utils import YamlDict


class ConfiguredApp(NamedTuple):
    app: AppCR
    app_cm: Optional[ConfigMap]


AppFactoryFunc = Callable[..., ConfiguredApp]


def app_factory_func(
    kube_client: HTTPClient,
    app_catalog_factory: AppCatalogFactoryFunc,
    namespace_factory: NamespaceFactoryFunc,
    created_apps: List[ConfiguredApp],
) -> AppFactoryFunc:
    def _app_factory(
        app_name: str,
        app_version: str,
        catalog_name: str,
        catalog_url: str,
        namespace: str = "default",
        deployment_namespace: str = "default",
        config_values: YamlDict = None,
        namespace_config_annotations: YamlDict = None,
        namespace_config_labels: YamlDict = None,
        timeout_sec: int = 60,
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
        assert catalog_url != ""

        api_version = "application.giantswarm.io/v1alpha1"
        app_cm_name = "{}-testing-user-config".format(app_name)
        catalog = app_catalog_factory(catalog_name, catalog_url)
        namespace_factory(namespace)
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
                "catalog": catalog.metadata["name"],
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
        created_apps.append(ConfiguredApp(app_obj, app_cm_obj))
        if timeout_sec > 0:
            wait_for_apps_to_run(kube_client, [app_name], namespace, timeout_sec)

        # we return a new object here, so that user doesn't alter the one added to created_apps
        return ConfiguredApp(app_obj, app_cm_obj)

    return _app_factory
