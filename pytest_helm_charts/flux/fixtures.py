from time import sleep
from typing import Iterable, TypeVar, Callable, Type, List

import pykube
import pytest

from pytest_helm_charts.api.deployment import wait_for_deployments_to_run
from pytest_helm_charts.clusters import Cluster
from pytest_helm_charts.flux.git_repository import (
    GitRepositoryCR,
    GitRepositoryFactoryFunc,
    git_repository_factory_func,
)
from pytest_helm_charts.flux.helm_release import HelmReleaseCR, HelmReleaseFactoryFunc, helm_release_factory_func
from pytest_helm_charts.flux.helm_repository import (
    HelmRepositoryCR,
    HelmRepositoryFactoryFunc,
    helm_repository_factory_func,
)
from pytest_helm_charts.flux.kustomization import KustomizationCR, KustomizationFactoryFunc, kustomization_factory_func
from pytest_helm_charts.flux.utils import NamespacedFluxCR

FLUX_NAMESPACE_NAME = "default"
FLUX_DEPLOYMENTS_READY_TIMEOUT: int = 180


@pytest.fixture(scope="module")
def flux_deployments(kube_cluster: Cluster) -> List[pykube.Deployment]:
    deployments = wait_for_deployments_to_run(
        kube_cluster.kube_client,
        [
            "helm-controller",
            "image-automation-controller",
            "image-reflector-controller",
            "kustomize-controller",
            "notification-controller",
            "source-controller",
        ],
        FLUX_NAMESPACE_NAME,
        FLUX_DEPLOYMENTS_READY_TIMEOUT,
    )
    return deployments


T = TypeVar("T", bound=NamespacedFluxCR)
FactoryFunc = Callable[..., T]
MetaFactoryFunc = Callable[[pykube.HTTPClient, List[T]], FactoryFunc]


def _flux_factory(kube_cluster: Cluster, meta_func: MetaFactoryFunc, obj_type: Type[T]) -> Iterable[FactoryFunc]:
    created_objects: List[T] = []

    yield meta_func(kube_cluster.kube_client, created_objects)

    for flux_object in created_objects:
        flux_object.delete()

    any_exists = True
    while any_exists:
        any_exists = False
        for o in created_objects:
            if getattr(obj_type, "objects")(kube_cluster.kube_client, namespace=o.namespace).get_or_none(name=o.name):
                any_exists = True
                sleep(0.1)
                break


@pytest.fixture(scope="module")
def kustomization_factory(kube_cluster: Cluster) -> Iterable[KustomizationFactoryFunc]:
    yield from _flux_factory(kube_cluster, kustomization_factory_func, KustomizationCR)


@pytest.fixture(scope="module")
def git_repository_factory(kube_cluster: Cluster) -> Iterable[GitRepositoryFactoryFunc]:
    for f in _flux_factory(kube_cluster, git_repository_factory_func, GitRepositoryCR):
        yield f


@pytest.fixture(scope="module")
def helm_repository_factory(
    kube_cluster: Cluster,
) -> Iterable[HelmRepositoryFactoryFunc]:
    for f in _flux_factory(kube_cluster, helm_repository_factory_func, HelmRepositoryCR):
        yield f


@pytest.fixture(scope="module")
def helm_release_factory(kube_cluster: Cluster) -> Iterable[HelmReleaseFactoryFunc]:
    for f in _flux_factory(kube_cluster, helm_release_factory_func, HelmReleaseCR):
        yield f
