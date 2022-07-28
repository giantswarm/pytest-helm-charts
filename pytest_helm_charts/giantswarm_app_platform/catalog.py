import logging
from typing import List, Optional, Protocol, Dict

from pykube import HTTPClient
from pykube.objects import NamespacedAPIObject

from pytest_helm_charts.k8s.fixtures import NamespaceFactoryFunc
from pytest_helm_charts.utils import inject_extra

logger = logging.getLogger(__name__)


class CatalogCR(NamespacedAPIObject):
    version = "application.giantswarm.io/v1alpha1"
    endpoint = "catalogs"
    kind = "Catalog"


class CatalogFactoryFunc(Protocol):
    def __call__(
        self,
        catalog_name: str,
        catalog_namespace: str,
        catalog_url: Optional[str],
        repositories_urls: Optional[List[str]] = None,
        extra_metadata: Optional[dict] = None,
        extra_spec: Optional[dict] = None,
    ) -> CatalogCR:
        ...


def make_catalog_obj(
    kube_client: HTTPClient,
    catalog_name: str,
    catalog_namespace: str,
    catalog_url: str,
    repositories_urls: Optional[List[str]] = None,
    extra_metadata: Optional[dict] = None,
    extra_spec: Optional[dict] = None,
) -> CatalogCR:
    repositories: List[Dict[str, str]] = []
    if repositories_urls:
        repositories = [{"URL": r, "type": "helm"} for r in repositories_urls]
    else:
        repositories = [{"URL": catalog_url, "type": "helm"}]

    catalog_obj = inject_extra(
        {
            "apiVersion": "application.giantswarm.io/v1alpha1",
            "kind": "Catalog",
            "metadata": {
                "name": catalog_name,
                "namespace": catalog_namespace,
            },
            "spec": {
                "description": "Catalog for testing.",
                "storage": {"URL": catalog_url, "type": "helm"},
                "repositories": repositories,
                "title": catalog_name,
                "logoURL": "https://my-org.github.com/logo.png",
            },
        },
        extra_metadata,
        extra_spec,
    )
    return CatalogCR(kube_client, catalog_obj)


def catalog_factory_func(
    kube_client: HTTPClient, objects: List[CatalogCR], namespace_factory: NamespaceFactoryFunc
) -> CatalogFactoryFunc:
    """Return a factory object, that can be used to configure new Catalog CRs
    for the 'app-operator' running in the cluster"""

    def _catalog_factory(
        catalog_name: str,
        catalog_namespace: str = "default",
        catalog_url: Optional[str] = None,
        repositories_urls: Optional[List[str]] = None,
        extra_metadata: Optional[dict] = None,
        extra_spec: Optional[dict] = None,
    ) -> CatalogCR:
        """A factory function used to create catalogs in the k8s API using Catalog CR.

        Args:
            catalog_name: name of the created Catalog CR. If the Catalog with this name already exists
                in the namespace but the URL is different, it's an error. If the URL and name
                are the same, nothing is done.
            catalog_namespace: namespace to create the Catalog CR in.
            catalog_url: URL of the catalog.
            repositories_urls: A list of additional repositories hosting the same catalog. If left at 'None',
                a single entry including `catalog_url` will be created.
            extra_metadata: any additional fields to be included in the 'metadata' section.
            extra_spec: any additional fields to be included in the 'Spec' section.

        Returns:
            CatalogCR created or found in the k8s API.

        Raises:
            ValueError: if catalog with the same name, but different URL already exists.

        """

        namespace_factory(catalog_namespace)
        if not catalog_url:
            catalog_url = "https://giantswarm.github.io/{}-catalog/".format(catalog_name)
        for c in objects:
            if c.metadata["name"] == catalog_name and c.metadata["namespace"] == catalog_namespace:
                existing_url = c.obj["spec"]["storage"]["URL"]
                if existing_url == catalog_url:
                    return c
                raise ValueError(
                    f"You requested creation of Catalog named {catalog_name} in namespace {catalog_namespace} "
                    f"with URL {catalog_url}, but it was already registered with another URL {existing_url}."
                )

        catalog = make_catalog_obj(
            kube_client, catalog_name, catalog_namespace, catalog_url, repositories_urls, extra_metadata, extra_spec
        )
        objects.append(catalog)
        catalog.create()
        logger.debug(f"Created Catalog '{catalog.namespace}/{catalog.name}'.")
        # TODO: once Catalog CR supports `status` fields, check here that the catalog is present
        return catalog

    return _catalog_factory
