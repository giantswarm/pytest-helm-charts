from pykube.objects import APIObject, NamespacedAPIObject


class AppCatalogCR(APIObject):
    version = "application.giantswarm.io/v1alpha1"
    endpoint = "appcatalogs"
    kind = "AppCatalog"


class CatalogCR(NamespacedAPIObject):
    version = "application.giantswarm.io/v1alpha1"
    endpoint = "catalogs"
    kind = "Catalog"


class AppCR(NamespacedAPIObject):
    version = "application.giantswarm.io/v1alpha1"
    endpoint = "apps"
    kind = "App"
