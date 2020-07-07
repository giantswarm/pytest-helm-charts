from typing import Callable, List, Optional

from pykube import HTTPClient

from .custom_resources import AppCatalogCR

AppCatalogFactoryFunc = Callable[[str, Optional[str]], AppCatalogCR]


def __get_app_catalog_obj(catalog_name: str, catalog_uri: str, kube_client: HTTPClient) -> AppCatalogCR:
    app_catalog_cr = {
        "apiVersion": "application.giantswarm.io/v1alpha1",
        "kind": "AppCatalog",
        "metadata": {
            "labels": {"app-operator.giantswarm.io/version": "1.0.0", "application.giantswarm.io/catalog-type": ""},
            "name": catalog_name,
        },
        "spec": {
            "description": "Catalog for testing.",
            "storage": {"URL": catalog_uri, "type": "helm"},
            "title": catalog_name,
        },
    }
    return AppCatalogCR(kube_client, app_catalog_cr)


def app_catalog_factory_func(
    kube_client: HTTPClient, created_app_catalogs: List[AppCatalogCR]
) -> AppCatalogFactoryFunc:
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
                    "{}".format(name, url, existing_url)
                )

        app_catalog = __get_app_catalog_obj(name, str(url), kube_client)
        created_app_catalogs.append(app_catalog)
        app_catalog.create()
        # TODO: check that app catalog is present
        return app_catalog

    return _app_catalog_factory
