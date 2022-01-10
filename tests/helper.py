from typing import Any

from _pytest.pytester import Testdir, RunResult
from pytest_mock import MockFixture


def run_pytest(testdir: Testdir, mocker: MockFixture, *args: Any) -> RunResult:
    mocker.patch("pytest_helm_charts.fixtures.ExistingCluster", autospec=True)
    result = testdir.runpytest(
        "--cluster-type",
        "existing",
        "--log-cli-level",
        "debug",
        "--kube-config",
        "/tmp/kat_test/kube.config",  # nosec
        '--chart-extra-info="key1=val1,external_cluster_type=kind"',
        "-v",
        *args,
    )
    # fnmatch_lines does an assertion internally
    result.stdout.fnmatch_lines(["*Cluster connection configured*", "*Cluster connection released*"])

    return result
