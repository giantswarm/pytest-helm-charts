from typing import Callable, Type

from pykube import HTTPClient
from pykube.objects import APIObject, object_factory

AppCRType = Type[APIObject]
AppCatalogCRType = Type[APIObject]
AppCR = APIObject
AppCatalogCR = APIObject
AppCatalogFactoryFunc = Callable[[str, str], AppCatalogCR]


class GiantSwarmAppPlatformCRs:
    def __init__(self, kube_client: HTTPClient):
        super().__init__()
        self.app_cr_factory: AppCRType = object_factory(
            kube_client, "application.giantswarm.io/v1alpha1", "App")
        self.app_catalog_cr_factory: AppCatalogCRType = object_factory(
            kube_client, "application.giantswarm.io/v1alpha1", "AppCatalog")


def get_app_catalog_obj(catalog_name: str, catalog_uri: str,
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
