from _pytest.pytester import Testdir
from pytest_mock import MockFixture

from tests.helper import run_pytest


def test_app_catalog_working_example(testdir: Testdir, mocker: MockFixture) -> None:
    testdir.copy_example("examples/test_giantswarm_app_platform.py")
    # catalog_name = "test-dynamic"
    # catalog_url = "https://test-dynamic.com"

    mocker.patch("pytest_helm_charts.giantswarm_app_platform.app_catalog.AppCatalogCR.create")
    # run pytest with the following cmd args
    result = run_pytest(testdir, mocker, "test_giantswarm_app_platform.py::test_app_catalog_factory_fixture")
    # TODO: assert AppCatalog was called with correct args

    # mock_app_catalog_cr.create.assert_called_once()
    assert result.ret == 0
