import os

import pytest
from _pytest.fixtures import FixtureRequest
from pytest_mock import MockFixture


def test_temp_namespace(request: FixtureRequest, mocker: MockFixture) -> None:
    ns_fixture = request.getfixturevalue("random_namespace")
    assert ns_fixture is not None
    ns_fixture.delete = mocker.MagicMock()


def test_kubeconfig_path_env_var(request: FixtureRequest) -> None:
    test_path = "env/kube.config"
    os.environ["KUBECONFIG"] = test_path
    kubeconfig_path = request.getfixturevalue("kube_config")
    assert kubeconfig_path == test_path


def test_kubeconfig_path_no_val(request: FixtureRequest) -> None:
    with pytest.raises(Exception) as e:
        request.getfixturevalue("kube_config")
        assert e.__str__().startswith("Environment variable 'KUBECONFIG'")
