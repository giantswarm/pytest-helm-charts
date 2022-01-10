import os
from pathlib import Path

from _pytest.config.argparsing import Parser

from pytest_helm_charts.k8s.fixtures import (  # noqa: F401
    namespace_factory,
    namespace_factory_function_scope,
    random_namespace,
    random_namespace_function_scope,
)
from pytest_helm_charts.fixtures import (  # noqa: F401
    chart_path,
    chart_version,
    chart_extra_info,
    test_extra_info,
    cluster_type,
    kube_cluster,
    kube_config,
    values_file_path,
    _existing_cluster_factory,
)
from pytest_helm_charts.giantswarm_app_platform.apps.http_testing import (  # noqa: F401
    gatling_app_factory,
    stormforger_load_app_factory,
)
from pytest_helm_charts.giantswarm_app_platform.fixtures import (  # noqa: F401
    app_catalog_factory,
    app_factory,
    app_factory_function_scope,
    catalog_factory,
    catalog_factory_function_scope,
)
from pytest_helm_charts.flux.fixtures import (  # noqa: F401
    flux_deployments,
    kustomization_factory,
    kustomization_factory_function_scope,
    git_repository_factory,
    git_repository_factory_function_scope,
    helm_repository_factory,
    helm_repository_factory_function_scope,
    helm_release_factory,
    helm_release_factory_function_scope,
)


def pytest_addoption(parser: Parser) -> None:
    group = parser.getgroup("helm-charts")
    group.addoption("--cluster-type", action="store", help="Pass information about cluster type being used for tests.")
    group.addoption(
        "--kube-config",
        action="store",
        default=os.path.join(str(Path.home()), ".kube", "config"),
        help="The path to 'kube.config' file. Used when '--cluster-type existing' is used as well.",
    )
    group.addoption("--values-file", action="store", help="Path to the values file used for testing the chart.")
    group.addoption("--chart-path", action="store", help="The path to a helm chart under test.")
    group.addoption("--chart-version", action="store", help="Override chart version for the chart under test.")
    group.addoption(
        "--chart-extra-info",
        action="store",
        default="",
        help="Pass any additional info about the chart in the 'key1=val1,key2=val2' format",
    )
    group.addoption(
        "--test-extra-info",
        action="store",
        default="",
        help="Pass any additional info about the test in the 'key1=val1,key2=val2' format",
    )
