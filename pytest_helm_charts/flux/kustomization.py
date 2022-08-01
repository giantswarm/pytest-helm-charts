import logging
from typing import Protocol, Optional, Any, List, Dict

from pykube import HTTPClient

from pytest_helm_charts.k8s.fixtures import NamespaceFactoryFunc
from pytest_helm_charts.flux.utils import NamespacedFluxCR, FLUX_CR_READY_TIMEOUT_SEC, flux_cr_ready
from pytest_helm_charts.utils import wait_for_objects_condition, inject_extra


logger = logging.getLogger(__name__)


class KustomizationCR(NamespacedFluxCR):
    version = "kustomize.toolkit.fluxcd.io/v1beta2"
    endpoint = "kustomizations"
    kind = "Kustomization"


class KustomizationFactoryFunc(Protocol):
    def __call__(
        self,
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
        ...


def kustomization_factory_func(
    kube_client: HTTPClient, namespace_factory: NamespaceFactoryFunc, created_kustomizations: List[KustomizationCR]
) -> KustomizationFactoryFunc:
    """Return a factory object, that can be used to create a new Kustomization CRs"""

    def _kustomization_factory(
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
        """A factory function used to create Flux Kustomizations.
        Args:
            name: name of the created Kustomization CR.
            namespace: namespace to create the Kustomization CR in.
            prune: enables garbage collection.
            interval: the interval at which to reconcile the Kustomization.
            repo_path: path to the directory containing the kustomization.yaml file.
            git_repository_name: name of the GitRepository object to get this kustomization from.
            timeout: timeout for apply and health checking operations.
            service_account_name: the name of the Kubernetes service account to impersonate
                when reconciling this Kustomization.
            extra_metadata: a dictionary of any additional attributes to put directly into "metadata"
                part of the object
            extra_spec: a dictionary of any additional attributes to put directly into "spec"
                part of the object
        Returns:
            KustomizationCR created or found in the k8s API.
        Raises:
            ValueError: if object with the same name already exists.
        """
        for k in created_kustomizations:
            if k.metadata["name"] == name and k.metadata["namespace"] == namespace:
                return k

        namespace_factory(namespace)
        kustomization = make_kustomization_obj(
            kube_client,
            name,
            namespace,
            prune,
            interval,
            repo_path,
            git_repository_name,
            timeout,
            service_account_name,
            extra_metadata=extra_metadata,
            extra_spec=extra_spec,
        )
        created_kustomizations.append(kustomization)
        kustomization.create()
        logger.debug(f"Created Flux Kustomization '{kustomization.namespace}/{kustomization.name}'.")
        wait_for_kustomizations_to_be_ready(kube_client, [name], namespace, FLUX_CR_READY_TIMEOUT_SEC, missing_ok=True)
        return kustomization

    return _kustomization_factory


def make_kustomization_obj(
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
    cr: Dict[str, Any] = {
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

    cr = inject_extra(cr, extra_metadata, extra_spec)
    return KustomizationCR(kube_client, cr)


def wait_for_kustomizations_to_be_ready(
    kube_client: HTTPClient,
    kustomization_names: List[str],
    kustomization_namespace: str,
    timeout_sec: int,
    missing_ok: bool = False,
) -> List[KustomizationCR]:
    """Block until all Kustomization objects in `kustomization_names` have status 'Ready'."""
    objects = wait_for_objects_condition(
        kube_client,
        KustomizationCR,
        kustomization_names,
        kustomization_namespace,
        flux_cr_ready,
        timeout_sec,
        missing_ok,
    )
    return objects
