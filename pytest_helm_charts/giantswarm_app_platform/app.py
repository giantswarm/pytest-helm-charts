from typing import Callable, List, NamedTuple, Optional

import yaml
from pykube import HTTPClient, ConfigMap

from .app_catalog import AppCatalogFactoryFunc
from .custom_resources import AppCR
from ..utils import YamlDict


class ConfiguredApp(NamedTuple):
    app: AppCR
    app_cm: Optional[ConfigMap]


AppFactoryFunc = Callable[[str, str, str, str, str, YamlDict], ConfiguredApp]


def app_factory_func(
    kube_client: HTTPClient, app_catalog_factory: AppCatalogFactoryFunc, created_apps: List[ConfiguredApp]
) -> AppFactoryFunc:
    def _app_factory(
        app_name: str,
        app_version: str,
        catalog_name: str,
        catalog_url: str,
        namespace: str = "default",
        config_values: YamlDict = None,
    ) -> ConfiguredApp:
        # TODO: include proper regexp validation
        if config_values is None:
            config_values = {}
        assert app_name != ""
        assert app_version != ""
        assert catalog_name != ""
        assert catalog_url != ""

        api_version = "application.giantswarm.io/v1alpha1"
        app_cm_name = "{}-testing-user-config".format(app_name)
        catalog = app_catalog_factory(catalog_name, catalog_url)
        kind = "App"

        app: YamlDict = {
            "apiVersion": api_version,
            "kind": kind,
            "metadata": {
                "name": app_name,
                "namespace": namespace,
                "labels": {"app": app_name, "app-operator.giantswarm.io/version": "1.0.0"},
            },
            "spec": {
                "catalog": catalog.metadata["name"],
                "version": app_version,
                "kubeConfig": {"inCluster": True},
                "name": app_name,
                "namespace": namespace,
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
        # TODO: wait until deployment is all ready
        # we return a new object here, so that user doesn't alter the one added to created_apps
        return ConfiguredApp(app_obj, app_cm_obj)

    return _app_factory
