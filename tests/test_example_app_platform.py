from _pytest.pytester import Testdir
from pytest_mock import MockFixture

from tests.helper import run_pytest


def test_app_catalog_working_example(testdir: Testdir, mocker: MockFixture):
    testdir.copy_example("examples/test_giantswarm_app_platform.py")
    # catalog_name = "test-dynamic"
    # catalog_url = "https://test-dynamic.com"

    mocker.patch("pytest_helm_charts.giantswarm_app_platform.app_catalog.AppCatalogCR.create")
    # run pytest with the following cmd args
    result = run_pytest(testdir, mocker, "test_giantswarm_app_platform.py::test_app_catalog_factory_fixture")
    # TODO: assert AppCatalog was called with correct args

    # mock_app_catalog_cr.create.assert_called_once()
    assert result.ret == 0


# def test_app_loadtest_app_working(testdir: Testdir, mocker: MockFixture):
#     testdir.copy_example("examples/test_giantswarm_app_platform.py")
#     catalog_name = "test-dynamic"
#     catalog_url = "https://test-dynamic.com"
#     mock_app_catalog_cr = mocker.Mock(name="MockAppCR")
#     mock_app_catalog_cr.metadata = {"name": catalog_name}
#     mock_app_catalog_cr.obj = {
#         "spec": {
#             "title": catalog_name,
#             "storage": {
#                 "type": "helm",
#                 "URL": catalog_url,
#             }
#         }
#     }
#     mock_app_catalog_cr_type = mocker.Mock(name="MockAppCRType")
#     mock_app_catalog_cr_type.return_value = mock_app_catalog_cr
#     mocker.patch("pytest_helm_charts.giantswarm_app_platform.custom_resources.object_factory", autospec=True)
#     pytest_helm_charts.giantswarm_app_platform.custom_resources.object_factory.return_value = mock_app_catalog_cr_type
#
#     # run pytest with the following cmd args
#     result = run_pytest(testdir, mocker, "test_giantswarm_app_platform.py::test_app_catalog_factory_fixture")
#
#     mock_app_catalog_cr.create.assert_called_once()
#     assert result.ret == 0
