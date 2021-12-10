from pykube.objects import APIObject, NamespacedAPIObject
from deprecated import deprecated


@deprecated(version="0.5.3", reason="Please use `CatalogCR` instead.")
class AppCatalogCR(APIObject):
    version = "application.giantswarm.io/v1alpha1"
    endpoint = "appcatalogs"
    kind = "AppCatalog"


class CatalogCR(NamespacedAPIObject):
    version = "application.giantswarm.io/v1alpha1"
    endpoint = "catalogs"
    kind = "Catalog"
