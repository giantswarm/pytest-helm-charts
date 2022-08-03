import os
from pathlib import Path

from _pytest.config.argparsing import Parser

from pytest_helm_charts.fixtures import (  # noqa: F401
    chart_path,
    chart_version,
    test_extra_info,
    cluster_type,
    kube_cluster,
    kube_config,
    values_file_path,
    get_cmd_line_option_name_from_env_var,
    CMD_VAR_TEST_EXTRA_INFO,
    ENV_VAR_CHART_PATH,
    ENV_VAR_CHART_VERSION,
    ENV_VAR_CLUSTER_TYPE,
    ENV_VAR_CLUSTER_VERSION,
    ENV_VAR_KUBE_CONFIG,
    ENV_VAR_APP_CONFIG_PATH,
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
from pytest_helm_charts.k8s.fixtures import (  # noqa: F401
    namespace_factory,
    namespace_factory_function_scope,
    random_namespace,
    random_namespace_function_scope,
)


def _get_cmd_line_option_full_name(env_var_name: str) -> str:
    cmd_name = get_cmd_line_option_name_from_env_var(env_var_name)
    cmd_name = cmd_name.replace("_", "-")
    return "--" + cmd_name


def pytest_addoption(parser: Parser) -> None:
    group = parser.getgroup("pytest-helm-charts")
    group.addoption(
        _get_cmd_line_option_full_name(ENV_VAR_CHART_PATH), action="store", help="The path to a helm chart under test."
    )
    group.addoption(
        _get_cmd_line_option_full_name(ENV_VAR_CHART_VERSION),
        action="store",
        help="Override chart version for the chart under test.",
    )
    group.addoption(
        _get_cmd_line_option_full_name(ENV_VAR_CLUSTER_TYPE),
        action="store",
        help="Pass information about cluster type being used for tests.",
    )
    group.addoption(
        _get_cmd_line_option_full_name(ENV_VAR_CLUSTER_VERSION),
        action="store",
        help="Pass information about k8s version being used for tests.",
    )
    group.addoption(
        _get_cmd_line_option_full_name(ENV_VAR_KUBE_CONFIG),
        action="store",
        default=os.path.join(str(Path.home()), ".kube", "config"),
        help="The path to 'kube config' file.",
    )
    group.addoption(
        _get_cmd_line_option_full_name(ENV_VAR_APP_CONFIG_PATH),
        action="store",
        help="Path to the values file used for testing the chart.",
    )
    group.addoption(
        "--" + CMD_VAR_TEST_EXTRA_INFO,
        action="store",
        default="",
        help="Pass any additional info about the test in the 'key1=val1,key2=val2' format",
    )
