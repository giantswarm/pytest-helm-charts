from typing import Type

from pykube import HTTPClient, object_factory
from pykube.objects import APIObject

AppCatalogCRType = Type[APIObject]
AppCatalogCR = APIObject
AppCRType = Type[APIObject]
AppCR = APIObject


class GiantSwarmAppPlatformCRs:
    def __init__(self, kube_client: HTTPClient):
        super().__init__()
        self.app_cr_factory: AppCRType = object_factory(
            kube_client, "application.giantswarm.io/v1alpha1", "App")
        self.app_catalog_cr_factory: AppCatalogCRType = object_factory(
            kube_client, "application.giantswarm.io/v1alpha1", "AppCatalog")
