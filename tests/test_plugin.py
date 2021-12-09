# noinspection PyProtectedMember
from pytest_helm_charts.fixtures import _parse_extra_info  # noqa: F401


def test_parse_chart_extra_info() -> None:
    res = _parse_extra_info("key1=val1,external_cluster_type=kind")
    assert len(res) == 2
    assert "key1" in res and res["key1"] == "val1"
    assert "external_cluster_type" in res and res["external_cluster_type"] == "kind"


def test_parse_chart_no_extra_info() -> None:
    res = _parse_extra_info("")
    assert len(res) == 0
