from typing import Iterable, List

import pykube
import pytest

from pytest_helm_charts.api.deployment import wait_for_deployments_to_run
from pytest_helm_charts.api.fixtures import NamespaceFactoryFunc
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
from pytest_helm_charts.utils import delete_and_wait_for_objects

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


@pytest.fixture(scope="function")
def kustomization_factory_function_scope(
    kube_cluster: Cluster, namespace_factory: NamespaceFactoryFunc
) -> Iterable[KustomizationFactoryFunc]:
    yield from _kustomization_factory_impl(kube_cluster, namespace_factory)


@pytest.fixture(scope="module")
def kustomization_factory(
    kube_cluster: Cluster, namespace_factory: NamespaceFactoryFunc
) -> Iterable[KustomizationFactoryFunc]:
    yield from _kustomization_factory_impl(kube_cluster, namespace_factory)


def _kustomization_factory_impl(
    kube_cluster: Cluster, namespace_factory: NamespaceFactoryFunc
) -> Iterable[KustomizationFactoryFunc]:
    created_objects: List[KustomizationCR] = []

    yield kustomization_factory_func(kube_cluster.kube_client, namespace_factory, created_objects)

    delete_and_wait_for_objects(kube_cluster.kube_client, KustomizationCR, created_objects)


@pytest.fixture(scope="function")
def git_repository_factory_function_scope(
    kube_cluster: Cluster, namespace_factory: NamespaceFactoryFunc
) -> Iterable[GitRepositoryFactoryFunc]:
    yield from _git_repository_factory_impl(kube_cluster, namespace_factory)


@pytest.fixture(scope="module")
def git_repository_factory(
    kube_cluster: Cluster, namespace_factory: NamespaceFactoryFunc
) -> Iterable[GitRepositoryFactoryFunc]:
    yield from _git_repository_factory_impl(kube_cluster, namespace_factory)


def _git_repository_factory_impl(
    kube_cluster: Cluster, namespace_factory: NamespaceFactoryFunc
) -> Iterable[GitRepositoryFactoryFunc]:
    created_objects: List[GitRepositoryCR] = []

    yield git_repository_factory_func(kube_cluster.kube_client, namespace_factory, created_objects)

    delete_and_wait_for_objects(kube_cluster.kube_client, GitRepositoryCR, created_objects)


@pytest.fixture(scope="function")
def helm_repository_factory_function_scope(
    kube_cluster: Cluster, namespace_factory: NamespaceFactoryFunc
) -> Iterable[HelmRepositoryFactoryFunc]:
    yield from _helm_repository_factory_impl(kube_cluster, namespace_factory)


@pytest.fixture(scope="module")
def helm_repository_factory(
    kube_cluster: Cluster, namespace_factory: NamespaceFactoryFunc
) -> Iterable[HelmRepositoryFactoryFunc]:
    yield from _helm_repository_factory_impl(kube_cluster, namespace_factory)


def _helm_repository_factory_impl(
    kube_cluster: Cluster, namespace_factory: NamespaceFactoryFunc
) -> Iterable[HelmRepositoryFactoryFunc]:
    created_objects: List[HelmRepositoryCR] = []

    yield helm_repository_factory_func(kube_cluster.kube_client, namespace_factory, created_objects)

    delete_and_wait_for_objects(kube_cluster.kube_client, HelmRepositoryCR, created_objects)


@pytest.fixture(scope="function")
def helm_release_factory_function_scope(
    kube_cluster: Cluster, namespace_factory: NamespaceFactoryFunc
) -> Iterable[HelmReleaseFactoryFunc]:
    yield from _helm_release_factory_impl(kube_cluster, namespace_factory)


@pytest.fixture(scope="module")
def helm_release_factory(
    kube_cluster: Cluster, namespace_factory: NamespaceFactoryFunc
) -> Iterable[HelmReleaseFactoryFunc]:
    yield from _helm_release_factory_impl(kube_cluster, namespace_factory)


def _helm_release_factory_impl(
    kube_cluster: Cluster, namespace_factory: NamespaceFactoryFunc
) -> Iterable[HelmReleaseFactoryFunc]:
    created_objects: List[HelmReleaseCR] = []

    yield helm_release_factory_func(kube_cluster.kube_client, namespace_factory, created_objects)

    delete_and_wait_for_objects(kube_cluster.kube_client, HelmReleaseCR, created_objects)
