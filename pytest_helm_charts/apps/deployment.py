from typing import Callable, List, NamedTuple, Optional

import yaml
from pykube import HTTPClient, ConfigMap

from .app_catalog import AppCR, GiantSwarmAppPlatformCRs, AppCatalogCR
from ..utils import YamlDict

AppCatalogFactoryFunc = Callable[[str, str], AppCatalogCR]


def __get_app_catalog_obj(catalog_name: str, catalog_uri: str,
                          kube_client: HTTPClient) -> AppCatalogCR:
    app_catalog_cr = {
        "apiVersion": "application.giantswarm.io/v1alpha1",
        "kind": "AppCatalog",
        "metadata": {
            "labels": {
                "app-operator.giantswarm.io/version": "1.0.0",
                "application.giantswarm.io/catalog-type": "",
            },
            "name": catalog_name,
        },
        "spec": {
            "description": "Catalog for testing.",
            "storage": {
                "URL": catalog_uri,
                "type": "helm",
            },
            "title": catalog_name,
        }
    }
    crs = GiantSwarmAppPlatformCRs(kube_client)
    return crs.app_catalog_cr_factory(kube_client, app_catalog_cr)


def app_catalog_factory_func(kube_client: HTTPClient,
                             created_app_catalogs: List[AppCatalogCR]) -> AppCatalogFactoryFunc:
    """Return a factory object, that can be used to configure new AppCatalog CRs
    for the 'app-operator' running in the cluster"""

    def _app_catalog_factory(name: str, url: Optional[str] = "") -> AppCatalogCR:
        if url == "":
            url = "https://giantswarm.github.io/{}-catalog/".format(name)
        for c in created_app_catalogs:
            if c.metadata["name"] == name:
                existing_url = c.obj["spec"]["storage"]["URL"]
                if existing_url == url:
                    return c
                raise ValueError(
                    "You requested creation of AppCatalog named {} with URL {} but it was already registered with URL "
                    "{}".format(name, url, existing_url))

        app_catalog = __get_app_catalog_obj(name, str(url), kube_client)
        created_app_catalogs.append(app_catalog)
        app_catalog.create()
        # TODO: check that app catalog is present
        return app_catalog

    return _app_catalog_factory


AppFactoryFunc = Callable[[str, str, str, str, str, YamlDict], AppCR]


class AppState(NamedTuple):
    app: AppCR
    app_cm: ConfigMap


def app_factory_func(kube_client: HTTPClient,
                     app_catalog_factory: AppCatalogFactoryFunc,
                     created_apps: List[AppState]) -> AppFactoryFunc:
    def _app_factory(app_name: str, app_version: str, catalog_name: str,
                     catalog_url: str, namespace: str = "default",
                     config_values: YamlDict = None) -> AppCR:
        # TODO: include proper regexp validation
        if config_values is None:
            config_values = {}
        assert app_name is not ""
        assert app_version is not ""
        assert catalog_name is not ""
        assert catalog_url is not ""

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
                "labels": {
                    "app": app_name,
                    "app-operator.giantswarm.io/version": "1.0.0"
                },
            },
            "spec": {
                "catalog": catalog.metadata["name"],
                "version": app_version,
                "kubeConfig": {
                    "inCluster": True
                },
                "name": app_name,
                "namespace": namespace,
            }
        }

        app_cm_obj: Optional[ConfigMap] = None
        if config_values:
            app["spec"]["config"] = {
                "configMap": {
                    "name": app_cm_name,
                    "namespace": namespace,
                }
            }
            app_cm: YamlDict = {
                "apiVersion": "v1",
                "kind": "ConfigMap",
                "metadata": {
                    "name": app_cm_name,
                    "namespace": namespace,
                },
                "data": {
                    "values": yaml.dump(config_values)
                }
            }
            app_cm_obj = ConfigMap(kube_client, app_cm)
            app_cm_obj.create()

        app_obj = GiantSwarmAppPlatformCRs(
            kube_client).app_cr_factory(kube_client, app)
        app_obj.create()
        created_apps.append(AppState(app_obj, app_cm_obj))
        # TODO: wait until deployment is all ready
        return app_obj

    return _app_factory
