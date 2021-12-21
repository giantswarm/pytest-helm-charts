from time import sleep
from typing import Iterable, TypeVar, Callable, Type

import pykube
import pytest

from pytest_helm_charts.api.deployment import wait_for_deployments_to_run
from pytest_helm_charts.clusters import Cluster

from custom_resources import (
    NamespacedFluxCR,
    KustomizationCR,
    GitRepositoryCR,
    HelmRepositoryCR,
    HelmReleaseCR,
)
from pytest_helm_charts.flux.fixture_helpers import (
    KustomizationFactoryFunc,
    kustomization_factory_func,
    GitRepositoryFactoryFunc,
    git_repository_factory_func,
    HelmRepositoryFactoryFunc,
    helm_repository_factory_func,
    HelmReleaseFactoryFunc,
    helm_release_factory_func,
)

FLUX_NAMESPACE_NAME = "default"
FLUX_DEPLOYMENT_TIMEOUT: int = 180


# scope "module" means this is run only once, for the first test case requesting! It might be tricky
# if you want to assert this multiple times
@pytest.fixture(scope="module")
def flux_deployments(kube_cluster: Cluster) -> list[pykube.Deployment]:
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
        FLUX_DEPLOYMENT_TIMEOUT,
    )
    return deployments


T = TypeVar("T", bound=NamespacedFluxCR)
FactoryFunc = Callable[..., T]
MetaFactoryFunc = Callable[[pykube.HTTPClient, list[T]], FactoryFunc]


def _flux_factory(kube_cluster: Cluster, meta_func: MetaFactoryFunc, obj_type: Type[T]) -> Iterable[FactoryFunc]:
    created_objects: list[T] = []

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
    for f in _flux_factory(kube_cluster, kustomization_factory_func, KustomizationCR):
        yield f


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
