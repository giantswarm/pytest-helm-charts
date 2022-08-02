import os
from typing import Any

from _pytest.pytester import RunResult
from pytest import Pytester
from pytest_mock import MockFixture


def run_pytest(pytester: Pytester, mocker: MockFixture, *args: Any) -> RunResult:
    mocker.patch("pytest_helm_charts.fixtures.ExistingCluster", autospec=True)
    mocker.patch.dict(
        os.environ,
        {
            "KUBECONFIG": "/tmp/kat_test/kube.config",  # nosec: this is not used, mock value only
            "ATS_CLUSTER_TYPE": "existing",
            "ATS_EXTRA_EXTERNAL_CLUSTER_TYPE": "kind",
        },
        clear=True,
    )
    result = pytester.runpytest(
        "--log-cli-level",
        "debug",
        "-v",
        *args,
    )
    # fnmatch_lines does an assertion internally
    result.stdout.fnmatch_lines(["*Cluster connection configured*", "*Cluster connection released*"])

    return result
