from unittest.mock import create_autospec

import pykube
from pytest import Pytester
from pytest_mock import MockFixture

from tests.helper import run_pytest


def test_api_working_example(pytester: Pytester, mocker: MockFixture) -> None:
    """Make sure that existing cluster is created using the correct config file."""
    pytester.copy_example("examples/test_basic_cluster.py")
    mocker.patch("pykube.Node.objects", autospec=True)
    mock_node = create_autospec("pykube.Node")
    pykube.Node.objects.return_value = [mock_node]

    result = run_pytest(pytester, mocker, "test_basic_cluster.py::test_api_working")

    pykube.Node.objects.assert_called_once()
    assert result.ret == 0


def test_cluster_info_example(pytester: Pytester, mocker: MockFixture) -> None:
    pytester.copy_example("examples/test_basic_cluster.py")
    result = run_pytest(pytester, mocker, "test_basic_cluster.py::test_cluster_info")
    result.stdout.fnmatch_lines(["*Running on cluster type existing*", "*external_cluster_type is kind*"])
