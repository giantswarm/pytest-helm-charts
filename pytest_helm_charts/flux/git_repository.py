import logging
from typing import Protocol, Optional, Any, List, Dict

from pykube import HTTPClient

from pytest_helm_charts.k8s.fixtures import NamespaceFactoryFunc
from pytest_helm_charts.flux.utils import NamespacedFluxCR, FLUX_CR_READY_TIMEOUT_SEC, flux_cr_ready
from pytest_helm_charts.utils import wait_for_objects_condition, inject_extra


logger = logging.getLogger(__name__)


class GitRepositoryCR(NamespacedFluxCR):
    version = "source.toolkit.fluxcd.io/v1beta1"
    endpoint = "gitrepositories"
    kind = "GitRepository"


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
    kube_client: HTTPClient, namespace_factory: NamespaceFactoryFunc, created_git_repositories: List[GitRepositoryCR]
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

        namespace_factory(namespace)
        git_repository = make_git_repository_obj(
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
        logger.debug(f"Created Flux GitRepository '{git_repository.namespace}/{git_repository.name}'.")
        wait_for_git_repositories_to_be_ready(
            kube_client, [name], namespace, FLUX_CR_READY_TIMEOUT_SEC, missing_ok=True
        )
        return git_repository

    return _git_repository_factory


def make_git_repository_obj(
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
    cr: Dict[str, Any] = {
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

    cr = inject_extra(cr, extra_metadata, extra_spec)
    return GitRepositoryCR(kube_client, cr)


def wait_for_git_repositories_to_be_ready(
    kube_client: HTTPClient,
    git_repo_names: List[str],
    git_repo_namespace: str,
    timeout_sec: int,
    missing_ok: bool = False,
) -> List[GitRepositoryCR]:
    """Block until all Git Repository objects in `git_repo_names` have status 'Ready'."""
    objects = wait_for_objects_condition(
        kube_client,
        GitRepositoryCR,
        git_repo_names,
        git_repo_namespace,
        flux_cr_ready,
        timeout_sec,
        missing_ok,
    )
    return objects
