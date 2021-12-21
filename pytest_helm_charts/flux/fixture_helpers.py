from typing import Optional, Protocol

from pykube import HTTPClient

from pytest_helm_charts.flux.custom_resources import (
    KustomizationCR,
    GitRepositoryCR,
    HelmRepositoryCR,
    HelmReleaseCR,
)
from pytest_helm_charts.flux.utils import (
    get_kustomization_obj,
    wait_for_kustomizations_to_be_ready,
    get_git_repository_obj,
    wait_for_git_repositories_to_be_ready,
    wait_for_helm_repositories_to_be_ready,
    get_helm_repository_obj,
    ChartTemplate,
    CrossNamespaceObjectReference,
    ValuesReference,
    get_helm_release_obj,
    wait_for_helm_releases_to_be_ready,
)

FLUX_CR_READY_TIMEOUT_SEC = 30


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
    kube_client: HTTPClient, created_kustomizations: list[KustomizationCR]
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

        kustomization = get_kustomization_obj(
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
        wait_for_kustomizations_to_be_ready(kube_client, [name], namespace, FLUX_CR_READY_TIMEOUT_SEC, missing_ok=True)
        return kustomization

    return _kustomization_factory


class GitRepositoryFactoryFunc(Protocol):
    def __call__(
        self,
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
        ...


def git_repository_factory_func(
    kube_client: HTTPClient, created_git_repositories: list[GitRepositoryCR]
) -> GitRepositoryFactoryFunc:
    """Return a factory object, that can be used to create a new GitRepository CRs"""

    def _git_repository_factory(
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
        """A factory function used to create Flux GitRepository.
        Args:
            name: name of the created GitRepository CR.
            namespace: namespace to create the GitRepository CR in.
            interval: the interval at which to check for repository updates.
            repo_url: the repository URL, can be a HTTP/S or SSH address.
            repo_branch: branch of the repo to use.
            secret_ref_name: the secret name containing the Git credentials.
                For HTTPS repositories the secret must contain username and password fields.
                For SSH repositories the secret must contain identity, identity.pub and known_hosts fields.
            ignore_pattern: Ignore overrides the set of excluded patterns in the .sourceignore format
                (which is the same as .gitignore). If not provided, a default will be used,
                consult the documentation for your version to find out what those are.
            extra_metadata: a dictionary of any additional attributes to put directly into "metadata"
                part of the object
            extra_spec: a dictionary of any additional attributes to put directly into "spec"
                part of the object
        Returns:
            GitRepositoryCR created or found in the k8s API.
        Raises:
            ValueError: if object with the same name already exists.
        """
        for gr in created_git_repositories:
            if gr.metadata["name"] == name and gr.metadata["namespace"] == namespace:
                return gr

        git_repository = get_git_repository_obj(
            kube_client,
            name,
            namespace,
            interval,
            repo_url,
            repo_branch,
            secret_ref_name,
            ignore_pattern,
            extra_metadata=extra_metadata,
            extra_spec=extra_spec,
        )
        created_git_repositories.append(git_repository)
        git_repository.create()
        wait_for_git_repositories_to_be_ready(
            kube_client, [name], namespace, FLUX_CR_READY_TIMEOUT_SEC, missing_ok=True
        )
        return git_repository

    return _git_repository_factory


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
    kube_client: HTTPClient, created_helm_repositories: list[HelmRepositoryCR]
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

        helm_repository = get_helm_repository_obj(
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
        wait_for_helm_repositories_to_be_ready(
            kube_client, [name], namespace, FLUX_CR_READY_TIMEOUT_SEC, missing_ok=True
        )
        return helm_repository

    return _helm_repository_factory


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
        depends_on: Optional[list[CrossNamespaceObjectReference]] = None,
        timeout: Optional[str] = None,
        values_from: Optional[list[ValuesReference]] = None,
        values: Optional[dict] = None,
        service_account_name: Optional[str] = None,
        extra_metadata: Optional[dict] = None,
        extra_spec: Optional[dict] = None,
    ) -> HelmReleaseCR:
        ...


def helm_release_factory_func(
    kube_client: HTTPClient, created_helm_releases: list[HelmReleaseCR]
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
        depends_on: Optional[list[CrossNamespaceObjectReference]] = None,
        timeout: Optional[str] = None,
        values_from: Optional[list[ValuesReference]] = None,
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

        helm_release = get_helm_release_obj(
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
        wait_for_helm_releases_to_be_ready(kube_client, [name], namespace, FLUX_CR_READY_TIMEOUT_SEC, missing_ok=True)
        return helm_release

    return _helm_release_factory
