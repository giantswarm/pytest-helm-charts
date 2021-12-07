from typing import List, Optional, Protocol

from pykube import HTTPClient

from pytest_helm_charts.giantswarm_app_platform.custom_resources import CatalogCR


class CatalogFactoryFunc(Protocol):
    def __call__(self, catalog_name: str, catalog_namespace: str, catalog_url: Optional[str]) -> CatalogCR:
        ...


def get_catalog_obj(catalog_name: str, catalog_namespace: str, catalog_url: str, kube_client: HTTPClient) -> CatalogCR:
    catalog_obj = {
        "apiVersion": "application.giantswarm.io/v1alpha1",
        "kind": "Catalog",
        "metadata": {
            "name": catalog_name,
            "namespace": catalog_namespace,
        },
        "spec": {
            "description": "Catalog for testing.",
            "storage": {"URL": catalog_url, "type": "helm"},
            "title": catalog_name,
            "logoURL": "https://my-org.github.com/logo.png",
        },
    }
    return CatalogCR(kube_client, catalog_obj)


def catalog_factory_func(kube_client: HTTPClient, created_catalogs: List[CatalogCR]) -> CatalogFactoryFunc:
    """Return a factory object, that can be used to configure new Catalog CRs
    for the 'app-operator' running in the cluster"""

    def _catalog_factory(
        catalog_name: str, catalog_namespace: str = "default", catalog_url: Optional[str] = ""
    ) -> CatalogCR:
        """A factory function used to create catalogs in the k8s API using Catalog CR.

        Args:
            catalog_name: name of the created Catalog CR. If the Catalog with this name already exists
                in the namespace but the URL is different, it's an error. If the URL and name
                are the same, nothing is done.
            catalog_namespace: namespace to create the Catalog CR in.
            catalog_url: URL of the catalog.

        Returns:
            CatalogCR created or found in the k8s API.

        Raises:
            ValueError: if catalog with the same name, but different URL already exists.

        """
        if catalog_url == "":
            catalog_url = "https://giantswarm.github.io/{}-catalog/".format(catalog_name)
        for c in created_catalogs:
            if c.metadata["name"] == catalog_name and c.metadata["namespace"] == catalog_namespace:
                existing_url = c.obj["spec"]["storage"]["URL"]
                if existing_url == catalog_url:
                    return c
                raise ValueError(
                    f"You requested creation of Catalog named {catalog_name} in namespace {catalog_namespace} "
                    f"with URL {catalog_url}, but it was already registered with another URL {existing_url}."
                )

        catalog = get_catalog_obj(catalog_name, catalog_namespace, str(catalog_url), kube_client)
        created_catalogs.append(catalog)
        catalog.create()
        # TODO: check that app catalog is present
        return catalog

    return _catalog_factory
