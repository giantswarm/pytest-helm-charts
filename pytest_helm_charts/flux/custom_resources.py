import abc

from pykube.objects import NamespacedAPIObject


# just to serve as a common interface
class NamespacedFluxCR(NamespacedAPIObject, abc.ABC):
    pass


class GitRepositoryCR(NamespacedFluxCR):
    version = "source.toolkit.fluxcd.io/v1beta1"
    endpoint = "gitrepositories"
    kind = "GitRepository"


class HelmRepositoryCR(NamespacedFluxCR):
    version = "source.toolkit.fluxcd.io/v1beta1"
    endpoint = "helmrepositories"
    kind = "HelmRepository"


class KustomizationCR(NamespacedFluxCR):
    version = "kustomize.toolkit.fluxcd.io/v1beta1"
    endpoint = "kustomizations"
    kind = "Kustomization"


class HelmReleaseCR(NamespacedFluxCR):
    version = "helm.toolkit.fluxcd.io/v2beta1"
    endpoint = "helmreleases"
    kind = "HelmRelease"
