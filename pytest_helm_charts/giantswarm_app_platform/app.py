from copy import deepcopy
from typing import Callable, List

from pykube import HTTPClient

from .app_catalog import AppCatalogFactoryFunc
from .entities import ConfiguredApp
from .utils import wait_for_apps_to_run, create_app
from ..fixtures import NamespaceFactoryFunc
from ..utils import YamlDict

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
        assert catalog_url != ""
        catalog = app_catalog_factory(catalog_name, catalog_url)
        namespace_factory(namespace)
        configured_app = create_app(
            kube_client,
            app_name,
            app_version,
            catalog.metadata["name"],
            namespace,
            deployment_namespace,
            config_values,
            namespace_config_annotations,
            namespace_config_labels,
        )
        created_apps.append(configured_app)
        if timeout_sec > 0:
            wait_for_apps_to_run(kube_client, [app_name], namespace, timeout_sec)

        # we return a new object here, so that user doesn't alter the one added to created_apps
        return deepcopy(configured_app)

    return _app_factory
