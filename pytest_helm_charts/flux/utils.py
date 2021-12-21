import logging
from dataclasses import dataclass, field, asdict
from typing import Optional, Any, List

from pykube import HTTPClient
from pytest_helm_charts.utils import wait_for_namespaced_objects_condition

from pytest_helm_charts.flux.custom_resources import (
    GitRepositoryCR,
    KustomizationCR,
    NamespacedFluxCR,
    HelmRepositoryCR,
    HelmReleaseCR,
)

logger = logging.getLogger(__name__)


def get_git_repository_obj(
    kube_client: HTTPClient,
    name: str,
    namespace: str,
    interval: str,
    repo_url: str,
    repo_branch: str = "master",
    secret_ref_name: Optional[str] = None,
    ignore_pattern: Optional[str] = None,
    extra_metadata: Optional[dict] = None,
    extra_spec: Optional[dict] = None,
) -> GitRepositoryCR:
    cr: dict[str, Any] = {
        "apiVersion": GitRepositoryCR.version,
        "kind": GitRepositoryCR.kind,
        "metadata": {
            "name": name,
            "namespace": namespace,
        },
        "spec": {
            "interval": interval,
            "url": repo_url,
            "ref": {
                "branch": repo_branch,
            },
        },
    }
    if secret_ref_name:
        cr["spec"]["secretRef"] = {
            "name": secret_ref_name,
        }
    if ignore_pattern:
        cr["spec"]["ignore"] = ignore_pattern

    if extra_metadata:
        cr["metadata"].update(extra_metadata)
    if extra_spec:
        cr["spec"].update(extra_spec)
    return GitRepositoryCR(kube_client, cr)


def get_kustomization_obj(
    kube_client: HTTPClient,
    name: str,
    namespace: str,
    prune: bool,
    interval: str,
    repo_path: str,
    git_repository_name: str,
    timeout: str,
    service_account_name: Optional[str] = None,
    extra_metadata: Optional[dict] = None,
    extra_spec: Optional[dict] = None,
) -> KustomizationCR:
    cr: dict[str, Any] = {
        "apiVersion": KustomizationCR.version,
        "kind": KustomizationCR.kind,
        "metadata": {
            "name": name,
            "namespace": namespace,
        },
        "spec": {
            "prune": prune,
            "interval": interval,
            "path": repo_path,
            "sourceRef": {
                "kind": "GitRepository",
                "name": git_repository_name,
            },
            "timeout": timeout,
        },
    }
    if service_account_name:
        cr["spec"]["serviceAccountName"] = service_account_name

    if extra_metadata:
        cr["metadata"].update(extra_metadata)
    if extra_spec:
        cr["spec"].update(extra_spec)
    return KustomizationCR(kube_client, cr)


def get_helm_repository_obj(
    kube_client: HTTPClient,
    name: str,
    namespace: str,
    interval: str,
    repo_url: str,
    secret_ref_name: Optional[str] = None,
    timeout: Optional[str] = None,
    suspend: bool = False,
    pass_credentials: bool = False,
    extra_metadata: Optional[dict] = None,
    extra_spec: Optional[dict] = None,
) -> HelmRepositoryCR:
    cr: dict[str, Any] = {
        "apiVersion": HelmRepositoryCR.version,
        "kind": HelmRepositoryCR.kind,
        "metadata": {
            "name": name,
            "namespace": namespace,
        },
        "spec": {
            "url": repo_url,
            "passCredentials": pass_credentials,
            "interval": interval,
            "suspend": suspend,
        },
    }
    if secret_ref_name:
        cr["spec"]["secretRef"] = {
            "name": secret_ref_name,
        }
    if timeout:
        cr["spec"]["timeout"] = timeout

    if extra_metadata:
        cr["metadata"].update(extra_metadata)
    if extra_spec:
        cr["spec"].update(extra_spec)
    return HelmRepositoryCR(kube_client, cr)


@dataclass
class CrossNamespaceObjectReference:
    kind: str
    name: str
    apiVersion: Optional[str] = None
    namespace: Optional[str] = None


@dataclass
class ChartTemplate:
    chart: str
    sourceRef: CrossNamespaceObjectReference
    version: Optional[str] = None
    valuesFiles: List[str] = field(default_factory=list)


@dataclass
class ValuesReference:
    kind: str
    name: str
    valuesKey: Optional[str] = None
    targetPath: Optional[str] = None
    optional: Optional[bool] = None


def get_helm_release_obj(
    kube_client: HTTPClient,
    name: str,
    namespace: str,
    chart: ChartTemplate,
    interval: str,
    suspend: bool = False,
    release_name: Optional[str] = None,
    target_namespace: Optional[str] = None,
    depends_on: Optional[List[CrossNamespaceObjectReference]] = None,
    timeout: Optional[str] = None,
    values_from: Optional[List[ValuesReference]] = None,
    values: Optional[dict] = None,
    service_account_name: Optional[str] = None,
    extra_metadata: Optional[dict] = None,
    extra_spec: Optional[dict] = None,
) -> HelmReleaseCR:
    cr: dict[str, Any] = {
        "apiVersion": HelmReleaseCR.version,
        "kind": HelmReleaseCR.kind,
        "metadata": {
            "name": name,
            "namespace": namespace,
        },
        "spec": {
            "chart": {"spec": asdict(chart)},
            "interval": interval,
            "suspend": suspend,
        },
    }
    if release_name:
        cr["spec"]["releaseName"] = release_name
    if target_namespace:
        cr["spec"]["targetNamespace"] = target_namespace
    if depends_on:
        cr["spec"]["dependsOn"] = [asdict(d) for d in depends_on]
    if timeout:
        cr["spec"]["timeout"] = timeout
    if values_from:
        cr["spec"]["valuesFrom"] = [asdict(v) for v in values_from]
    if values:
        cr["spec"]["values"] = values
    if service_account_name:
        cr["spec"]["serviceAccountName"] = service_account_name

    if extra_metadata:
        cr["metadata"].update(extra_metadata)
    if extra_spec:
        cr["spec"].update(extra_spec)
    return HelmReleaseCR(kube_client, cr)


def _flux_cr_ready(flux_obj: NamespacedFluxCR) -> bool:
    has_conditions = "status" in flux_obj.obj and "conditions" in flux_obj.obj["status"]
    if not has_conditions:
        return False
    conditions_count = len(flux_obj.obj["status"]["conditions"])
    if conditions_count == 0:
        return False
    if conditions_count > 1:
        logging.warning(
            f"Found '{conditions_count}' status conditions when expecting just 1. Using only"
            f" the first one on the list."
        )
    condition = flux_obj.obj["status"]["conditions"][0]
    return condition["type"] == "Ready" and condition["status"] == "True"


def wait_for_git_repositories_to_be_ready(
    kube_client: HTTPClient,
    git_repo_names: List[str],
    git_repo_namespace: str,
    timeout_sec: int,
    missing_ok: bool = False,
) -> List[GitRepositoryCR]:
    objects = wait_for_namespaced_objects_condition(
        kube_client,
        GitRepositoryCR,
        git_repo_names,
        git_repo_namespace,
        _flux_cr_ready,
        timeout_sec,
        missing_ok,
    )
    return objects


def wait_for_kustomizations_to_be_ready(
    kube_client: HTTPClient,
    kustomization_names: List[str],
    kustomization_namespace: str,
    timeout_sec: int,
    missing_ok: bool = False,
) -> List[KustomizationCR]:
    objects = wait_for_namespaced_objects_condition(
        kube_client,
        KustomizationCR,
        kustomization_names,
        kustomization_namespace,
        _flux_cr_ready,
        timeout_sec,
        missing_ok,
    )
    return objects


def wait_for_helm_repositories_to_be_ready(
    kube_client: HTTPClient,
    helm_repo_names: List[str],
    helm_repo_namespace: str,
    timeout_sec: int,
    missing_ok: bool = False,
) -> List[HelmRepositoryCR]:
    objects = wait_for_namespaced_objects_condition(
        kube_client,
        HelmRepositoryCR,
        helm_repo_names,
        helm_repo_namespace,
        _flux_cr_ready,
        timeout_sec,
        missing_ok,
    )
    return objects


def wait_for_helm_releases_to_be_ready(
    kube_client: HTTPClient,
    helm_release_names: List[str],
    helm_release_namespace: str,
    timeout_sec: int,
    missing_ok: bool = False,
) -> List[HelmReleaseCR]:
    objects = wait_for_namespaced_objects_condition(
        kube_client,
        HelmReleaseCR,
        helm_release_names,
        helm_release_namespace,
        _flux_cr_ready,
        timeout_sec,
        missing_ok,
    )
    return objects
