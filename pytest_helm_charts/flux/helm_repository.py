import logging
from typing import Protocol, Optional, Any, List, Dict

from pykube import HTTPClient

from pytest_helm_charts.k8s.fixtures import NamespaceFactoryFunc
from pytest_helm_charts.flux.utils import NamespacedFluxCR, FLUX_CR_READY_TIMEOUT_SEC, flux_cr_ready
from pytest_helm_charts.utils import wait_for_objects_condition, inject_extra


logger = logging.getLogger(__name__)


class HelmRepositoryCR(NamespacedFluxCR):
    version = "source.toolkit.fluxcd.io/v1beta1"
    endpoint = "helmrepositories"
    kind = "HelmRepository"


class HelmRepositoryFactoryFunc(Protocol):
    def __call__(
        self,
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
        ...


def helm_repository_factory_func(
    kube_client: HTTPClient, namespace_factory: NamespaceFactoryFunc, created_helm_repositories: List[HelmRepositoryCR]
) -> HelmRepositoryFactoryFunc:
    """Return a factory object, that can be used to create a new HelmRepository CRs"""

    def _helm_repository_factory(
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
        """A factory function used to create Flux HelmRepository.
        Args:
            name: name of the created Kustomization CR.
            namespace: namespace to create the Kustomization CR in.
            interval: the interval at which to check for repository updates.
            repo_url: the repository URL, can be a HTTP/S or SSH address.
            secret_ref_name: the secret name containing the Git credentials.
                For HTTPS repositories the secret must contain username and password fields.
                For SSH repositories the secret must contain identity, identity.pub and known_hosts fields.
            timeout: The timeout of index downloading, defaults to 60s.
            suspend: This flag tells the controller to suspend the reconciliation of this source.
            pass_credentials: PassCredentials allows the credentials from the SecretRef to be passed on to
                a host that does not match the host as defined in URL.
            extra_metadata: a dictionary of any additional attributes to put directly into "metadata"
                part of the object
            extra_spec: a dictionary of any additional attributes to put directly into "spec"
                part of the object
        Returns:
            HelmRepository created or found in the k8s API.
        Raises:
            ValueError: if object with the same name already exists.
        """
        for hr in created_helm_repositories:
            if hr.metadata["name"] == name and hr.metadata["namespace"] == namespace:
                return hr

        namespace_factory(namespace)
        helm_repository = make_helm_repository_obj(
            kube_client,
            name,
            namespace,
            interval,
            repo_url,
            secret_ref_name,
            timeout,
            suspend,
            pass_credentials,
            extra_metadata=extra_metadata,
            extra_spec=extra_spec,
        )
        created_helm_repositories.append(helm_repository)
        helm_repository.create()
        logger.debug(f"Created Flux HelmRepository '{helm_repository.namespace}/{helm_repository.name}'.")
        wait_for_helm_repositories_to_be_ready(
            kube_client, [name], namespace, FLUX_CR_READY_TIMEOUT_SEC, missing_ok=True
        )
        return helm_repository

    return _helm_repository_factory


def make_helm_repository_obj(
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
    cr: Dict[str, Any] = {
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

    cr = inject_extra(cr, extra_metadata, extra_spec)
    return HelmRepositoryCR(kube_client, cr)


def wait_for_helm_repositories_to_be_ready(
    kube_client: HTTPClient,
    helm_repo_names: List[str],
    helm_repo_namespace: str,
    timeout_sec: int,
    missing_ok: bool = False,
) -> List[HelmRepositoryCR]:
    """Block until all Helm Repository objects in `helm_repo_names` have status 'Ready'."""
    objects = wait_for_objects_condition(
        kube_client,
        HelmRepositoryCR,
        helm_repo_names,
        helm_repo_namespace,
        flux_cr_ready,
        timeout_sec,
        missing_ok,
    )
    return objects
