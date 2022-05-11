import logging
from typing import List, Optional, Protocol

from deprecated import deprecated
from pykube import HTTPClient
from pykube.objects import APIObject

from pytest_helm_charts.utils import inject_extra

logger = logging.getLogger(__name__)


@deprecated(version="0.5.3", reason="Please use `CatalogCR` instead.")
class AppCatalogCR(APIObject):
    version = "application.giantswarm.io/v1alpha1"
    endpoint = "appcatalogs"
    kind = "AppCatalog"


class AppCatalogFactoryFunc(Protocol):
    def __call__(
        self,
        catalog_name: str,
        catalog_url: Optional[str],
        extra_metadata: Optional[dict] = None,
        extra_spec: Optional[dict] = None,
    ) -> AppCatalogCR:
        ...


@deprecated(version="0.5.3", reason="Please use `catalog.get_catalog_obj()` instead.")
def make_app_catalog_object(
    kube_client: HTTPClient,
    catalog_name: str,
    catalog_url: str,
    extra_metadata: Optional[dict] = None,
    extra_spec: Optional[dict] = None,
) -> AppCatalogCR:
    app_catalog_cr = inject_extra(
        {
            "apiVersion": "application.giantswarm.io/v1alpha1",
            "kind": "AppCatalog",
            "metadata": {
                "labels": {"app-operator.giantswarm.io/version": "1.0.0", "application.giantswarm.io/catalog-type": ""},
                "name": catalog_name,
            },
            "spec": {
                "description": "Catalog for testing.",
                "storage": {"URL": catalog_url, "type": "helm"},
                "title": catalog_name,
                "logoURL": "https://my-org.github.com/logo.png",
            },
        },
        extra_metadata,
        extra_spec,
    )

    return AppCatalogCR(kube_client, app_catalog_cr)


@deprecated(version="0.5.3", reason="Please use `catalog.catalog_factory_func()` instead.")
def app_catalog_factory_func(
    kube_client: HTTPClient, created_app_catalogs: List[AppCatalogCR]
) -> AppCatalogFactoryFunc:
    """Return a factory object, that can be used to configure new AppCatalog CRs
    for the 'app-operator' running in the cluster"""

    def _app_catalog_factory(
        catalog_name: str,
        catalog_url: Optional[str] = None,
        extra_metadata: Optional[dict] = None,
        extra_spec: Optional[dict] = None,
    ) -> AppCatalogCR:
        """
        [Obsolete] Please use
        [_catalog_factory](pytest_helm_charts.giantswarm_app_platform.catalog._catalog_factory) instead.

        A factory function used to create catalogs in the k8s API using AppCatalog CR.

        Args:
            catalog_name: name of the created AppCatalog CR. If the name already exists and the URL is
                different, it's an error. If the URL and name are the same, nothing is done.
            catalog_url: URL of the catalog.

        Returns:
            AppCatalogCR created or found in the k8s API.

        Raises:
            ValueError: if catalog with the same name, but different URL already exists.

        """
        if not catalog_url:
            catalog_url = "https://giantswarm.github.io/{}-catalog/".format(catalog_name)
        for c in created_app_catalogs:
            if c.metadata["name"] == catalog_name:
                existing_url = c.obj["spec"]["storage"]["URL"]
                if existing_url == catalog_url:
                    return c
                raise ValueError(
                    "You requested creation of AppCatalog named {} with URL {} but it was already registered with URL "
                    "{}".format(catalog_name, catalog_url, existing_url)
                )

        app_catalog = make_app_catalog_object(kube_client, catalog_name, catalog_url, extra_metadata, extra_spec)
        created_app_catalogs.append(app_catalog)
        app_catalog.create()
        logger.debug(f"Created AppCatalog '{app_catalog.name}'.")
        return app_catalog

    return _app_catalog_factory
