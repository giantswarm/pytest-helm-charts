from copy import deepcopy
from typing import List, Protocol, Optional

from pykube import HTTPClient
from pytest_helm_charts.api.fixtures import NamespaceFactoryFunc
from pytest_helm_charts.giantswarm_app_platform.catalog import CatalogFactoryFunc
from pytest_helm_charts.giantswarm_app_platform.entities import ConfiguredApp
from pytest_helm_charts.giantswarm_app_platform.utils import wait_for_apps_to_run, create_app
from pytest_helm_charts.utils import YamlDict


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
                [CatalogCR](pytest_helm_charts.giantswarm_app_platform.custom_resources.CatalogCR);
                new catalog is created only when one with the same name doesn't already exist
             catalog_namespace: namespace where the catalog catalog_name is defined
             catalog_url: URL of the catalog to install the application from; this is used only if a catalog
                with the same name doesn't already exists (then a new catalog with the given name and URL is created
                in the k8s API)
             namespace: namespace where the App CR will be created
             deployment_namespace: namespace where the app will be deployed (can be different than `namespace`)
             config_values: any values that should be used to configure the app (same as `values.yaml` used for
                a Helm Chart directly).
             extra_metadata: optional dict that will be merged with the 'metadata:' section of the object
             extra_spec: optional dict that will be merged with the 'spec:' section of the object
             timeout_sec: timeout in seconds for the create operation

        Returns:
            The [ConfiguredApp](.entities.ConfiguredApp) object that includes both AppCR and ConfigMap created to
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
        if timeout_sec > 0:
            wait_for_apps_to_run(kube_client, [app_name], namespace, timeout_sec)

        # we return a new object here, so that user doesn't alter the one added to created_apps
        return deepcopy(configured_app)

    return _app_factory
