from _pytest.fixtures import FixtureRequest
from pytest_mock import MockFixture


def test_temp_namespace(request: FixtureRequest, mocker: MockFixture):
    ns_fixture = request.getfixturevalue("random_namespace")
    assert ns_fixture is not None
    ns_fixture.delete = mocker.MagicMock()
