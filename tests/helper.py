import unittest.mock

from _pytest.pytester import Testdir, RunResult
from pytest_mock import MockFixture


def run_pytest(testdir: Testdir, mocker: MockFixture, *args) -> RunResult:
    testdir.copy_example("conftest.py")
    mocker.patch('pytest_helm_charts.fixtures.ExistingCluster', autospec=True)
    result = testdir.runpytest(
        '--cluster-type',
        'existing',
        '--log-cli-level',
        'info',
        '--kube-config',
        '/tmp/kat_test/kube.config',
        '-v',
        *args
    )
    # fnmatch_lines does an assertion internally
    result.stdout.fnmatch_lines([
        '*Cluster created*',
        '*Cluster destroyed*',
    ])

    return result


def get_mock_app_catalog_cr(mocker: MockFixture, catalog_name: str, catalog_url: str) -> unittest.mock.Mock:
    mock_app_catalog_cr = mocker.Mock(name=f"MockAppCatalogCR-{catalog_name}")
    mock_app_catalog_cr.metadata = {"name": catalog_name}
    mock_app_catalog_cr.obj = {
        "spec": {
            "title": catalog_name,
            "storage": {
                "type": "helm",
                "URL": catalog_url,
            }
        }
    }
    return mock_app_catalog_cr


def get_mock_app_cr(mocker: MockFixture, app_name: str) -> unittest.mock.Mock:
    mock_app_cr = mocker.Mock(name=f"MockAppCR-{app_name}")
    mock_app_cr.metadata = {"name": app_name}
    mock_app_cr.obj = {
        "spec": {
        }
    }
    return mock_app_cr
