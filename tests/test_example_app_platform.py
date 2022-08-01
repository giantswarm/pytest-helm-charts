from pytest import Pytester
from pytest_mock import MockerFixture

from tests.helper import run_pytest
from tests.test_app_platform import mock_final_catalog_cleanup


def test_app_catalog_working_example(pytester: Pytester, mocker: MockerFixture) -> None:
    pytester.copy_example("examples/test_giantswarm_app_platform.py")
    # catalog_name = "test-dynamic"
    # catalog_url = "https://test-dynamic.com"

    mock_final_catalog_cleanup(mocker)
    mocker.patch("pykube.Namespace.create")
    mocker.patch("pytest_helm_charts.giantswarm_app_platform.catalog.CatalogCR.create")
    mocker.patch("pytest_helm_charts.giantswarm_app_platform.catalog.CatalogCR.delete")
    # run pytest with the following cmd args
    result = run_pytest(pytester, mocker, "test_giantswarm_app_platform.py::test_catalog_factory_fixture")
    # TODO: assert AppCatalog was called with correct args

    # mock_app_catalog_cr.create.assert_called_once()
    assert result.ret == 0
