from typing import Callable, List, Optional

from pykube import HTTPClient

from pytest_helm_charts.fixtures import NamespaceFactoryFunc
from pytest_helm_charts.giantswarm_app_platform.custom_resources import CatalogCR

CatalogFactoryFunc = Callable[[str, str, Optional[str]], CatalogCR]


def get_catalog_obj(catalog_name: str, catalog_namespace: str, catalog_uri: str, kube_client: HTTPClient) -> CatalogCR:
    catalog_obj = {
        "apiVersion": "application.giantswarm.io/v1alpha1",
        "kind": "Catalog",
        "metadata": {
            "name": catalog_name,
            "namespace": catalog_namespace,
        },
        "spec": {
            "description": "Catalog for testing.",
            "storage": {"URL": catalog_uri, "type": "helm"},
            "title": catalog_name,
            "logoURL": "https://my-org.github.com/logo.png",
        },
    }
    return CatalogCR(kube_client, catalog_obj)


def catalog_factory_func(
    kube_client: HTTPClient, namespace_factory: NamespaceFactoryFunc, created_catalogs: List[CatalogCR]
) -> CatalogFactoryFunc:
    """Return a factory object, that can be used to configure new Catalog CRs
    for the 'app-operator' running in the cluster"""

    def _catalog_factory(name: str, namespace: str = "default", url: Optional[str] = "") -> CatalogCR:
        """A factory function used to create catalogs in the k8s API using Catalog CR.

        Args:
            name: name of the created Catalog CR. If the Catalog with this name already exists
                in the namespace but the URL is different, it's an error. If the URL and name
                are the same, nothing is done.
            namespace: namespace to create the Catalog CR in.
            url: URL of the catalog.

        Returns:
            CatalogCR created or found in the k8s API.

        Raises:
            ValueError: if catalog with the same name, but different URL already exists.

        """
        if url == "":
            url = "https://giantswarm.github.io/{}-catalog/".format(name)
        for c in created_catalogs:
            if c.metadata["name"] == name and c.metadata["namespace"] == namespace:
                existing_url = c.obj["spec"]["storage"]["URL"]
                if existing_url == url:
                    return c
                raise ValueError(
                    f"You requested creation of Catalog named {name} in namespace {namespace} with URL {url},"
                    f" but it was already registered with another URL {existing_url}."
                )

        namespace_factory(namespace)
        catalog = get_catalog_obj(name, namespace, str(url), kube_client)
        created_catalogs.append(catalog)
        catalog.create()
        # TODO: check that app catalog is present
        return catalog

    return _catalog_factory
