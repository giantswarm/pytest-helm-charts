import os
from pathlib import Path

from _pytest.config.argparsing import Parser

from pytest_helm_charts.fixtures import _existing_cluster_factory  # noqa
from pytest_helm_charts.fixtures import chart_extra_info  # noqa
from pytest_helm_charts.fixtures import chart_path  # noqa
from pytest_helm_charts.fixtures import chart_version  # noqa
from pytest_helm_charts.fixtures import cluster_type  # noqa
from pytest_helm_charts.fixtures import kube_cluster  # noqa
from pytest_helm_charts.fixtures import namespace_factory  # noqa
from pytest_helm_charts.fixtures import random_namespace  # noqa
from pytest_helm_charts.fixtures import kube_config  # noqa
from pytest_helm_charts.fixtures import values_file_path  # noqa
from pytest_helm_charts.giantswarm_app_platform.apps.http_testing import gatling_app_factory  # noqa
from pytest_helm_charts.giantswarm_app_platform.apps.http_testing import stormforger_load_app_factory  # noqa
from pytest_helm_charts.giantswarm_app_platform.fixtures import app_catalog_factory  # noqa
from pytest_helm_charts.giantswarm_app_platform.fixtures import catalog_factory  # noqa
from pytest_helm_charts.giantswarm_app_platform.fixtures import app_factory  # noqa


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
