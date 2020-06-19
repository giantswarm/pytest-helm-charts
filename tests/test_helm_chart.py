from unittest.mock import create_autospec

import pykube
from _pytest.pytester import Testdir
from pytest_mock import MockFixture


def test_api_working_example(testdir: Testdir, mocker: MockFixture):
    """Make sure that existing cluster is created using the correct config file."""

    mocker.patch('pytest_helm_charts.fixtures.ExistingCluster', autospec=True)

    testdir.copy_example("examples/test_existing_cluster.py")
    mock_node = create_autospec("pykube.Node")
    mocker.patch('pykube.Node.objects', autospec=True)
    pykube.Node.objects.return_value = [mock_node]

    # run pytest with the following cmd args
    result = testdir.runpytest(
        '--cluster-type',
        'existing',
        '--log-cli-level',
        'info',
        '--kube-config',
        '/tmp/kat_test/kube.config',
        '-v'
    )

    pykube.Node.objects.assert_called_once()

    # fnmatch_lines does an assertion internally
    result.stdout.fnmatch_lines([
        '*Cluster created*',
        '*Cluster destroyed*',
    ])

    # make sure that that we get a '0' exit code for the testsuite
    assert result.ret == 0
