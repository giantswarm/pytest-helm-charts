import logging
from dataclasses import dataclass, field, asdict
from typing import Protocol, Optional, List, Any, Dict

from pykube import HTTPClient

from pytest_helm_charts.k8s.fixtures import NamespaceFactoryFunc
from pytest_helm_charts.flux.utils import NamespacedFluxCR, FLUX_CR_READY_TIMEOUT_SEC, flux_cr_ready
from pytest_helm_charts.utils import wait_for_objects_condition, inject_extra


logger = logging.getLogger(__name__)


class HelmReleaseCR(NamespacedFluxCR):
    version = "helm.toolkit.fluxcd.io/v2beta1"
    endpoint = "helmreleases"
    kind = "HelmRelease"


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


class HelmReleaseFactoryFunc(Protocol):
    def __call__(
        self,
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
        ...


def helm_release_factory_func(
    kube_client: HTTPClient, namespace_factory: NamespaceFactoryFunc, created_helm_releases: List[HelmReleaseCR]
) -> HelmReleaseFactoryFunc:
    """Return a factory object, that can be used to create a new HelmRelease CRs"""

    def _helm_release_factory(
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
        """A factory function used to create Flux HelmRepository.
        Args:
            name: name of the created Kustomization CR.
            namespace: namespace to create the Kustomization CR in.
            chart: Chart defines the template that should be created for this HelmRelease.
            interval: the interval at which to check for repository updates.
            suspend: This flag tells the controller to suspend the reconciliation of this source.
            release_name: Name used for the Helm release.
            target_namespace: Namespace to target when performing operations for the HelmRelease.
            depends_on: a list of CrossNamespaceObjectReference with
                references to HelmRelease resources that must be ready before this HelmRelease.
            timeout: The timeout of index downloading, defaults to 60s.
            values_from: References to resources containing Helm values for this HelmRelease,
                and information about how they should be merged.
            values: Holds the values for this Helm release.
            service_account_name: The name of the Kubernetes service account to impersonate
                when reconciling this HelmRelease.
            extra_metadata: a dictionary of any additional attributes to put directly into "metadata"
                part of the object
            extra_spec: a dictionary of any additional attributes to put directly into "spec"
                part of the object
        Returns:
            HelmRelease created or found in the k8s API.
        Raises:
            ValueError: if object with the same name already exists.
        """
        for hr in created_helm_releases:
            if hr.metadata["name"] == name and hr.metadata["namespace"] == namespace:
                return hr

        namespace_factory(namespace)
        if target_namespace:
            namespace_factory(target_namespace)
        helm_release = make_helm_release_obj(
            kube_client,
            name,
            namespace,
            chart,
            interval,
            suspend,
            release_name,
            target_namespace,
            depends_on,
            timeout,
            values_from,
            values,
            service_account_name,
            extra_metadata=extra_metadata,
            extra_spec=extra_spec,
        )
        created_helm_releases.append(helm_release)
        helm_release.create()
        logger.debug(f"Created Flux HelmRelease '{helm_release.namespace}/{helm_release.name}'.")
        wait_for_helm_releases_to_be_ready(kube_client, [name], namespace, FLUX_CR_READY_TIMEOUT_SEC, missing_ok=True)
        return helm_release

    return _helm_release_factory


def make_helm_release_obj(
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
    cr: Dict[str, Any] = {
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

    cr = inject_extra(cr, extra_metadata, extra_spec)
    return HelmReleaseCR(kube_client, cr)


def wait_for_helm_releases_to_be_ready(
    kube_client: HTTPClient,
    helm_release_names: List[str],
    helm_release_namespace: str,
    timeout_sec: int,
    missing_ok: bool = False,
) -> List[HelmReleaseCR]:
    """Block until all Helm Release objects in `helm_release_names` have status 'Ready'."""
    objects = wait_for_objects_condition(
        kube_client,
        HelmReleaseCR,
        helm_release_names,
        helm_release_namespace,
        flux_cr_ready,
        timeout_sec,
        missing_ok,
    )
    return objects
