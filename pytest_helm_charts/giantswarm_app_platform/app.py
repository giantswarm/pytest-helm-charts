from copy import deepcopy
from typing import Callable, List

from pykube import HTTPClient

from pytest_helm_charts.fixtures import NamespaceFactoryFunc
from pytest_helm_charts.giantswarm_app_platform.app_catalog import AppCatalogFactoryFunc
from pytest_helm_charts.giantswarm_app_platform.entities import ConfiguredApp
from pytest_helm_charts.giantswarm_app_platform.utils import wait_for_apps_to_run, create_app
from pytest_helm_charts.utils import YamlDict

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
        """Factory function used to create and deploy new apps using App CR. Calls are blocking.

        Args:
             app_name: name of the app in the app catalog
             app_version: version of the app to use from the app catalog
             catalog_name: a name of the catalog used for the
             [AppCatalogCR](pytest_helm_charts.giantswarm_app_platform.custom_resources.AppCatalogCR);
             new catalog is created only when one with the same name doesn't already exist
             catalog_url: URL of the catalog to install the application from; this is used only if a catalog
             with the same name doesn't already exists (then a new catalog with the given name and URL is created
             in the k8s API)
             namespace: namespace where the App CR will be created
             deployment_namespace: namespace where the app will be deployed (can be different than `namespace`)
             config_values: any values that should be used to configure the app (same as `values.yaml` used for
             a Helm Chart directly).
             namespace_config_annotations: a dictionary of annotations that need to be added to the
             `deployment_namespace` created for the app
             namespace_config_labels: a dictionary of labels that need to be added to the `deployment_namespace`
             created for the app
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
