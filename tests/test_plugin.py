from pytest_helm_charts.fixtures import _parse_extra_info  # noqa


def test_parse_chart_extra_info():
    res = _parse_extra_info("key1=val1,key2=val2")
    assert len(res) == 2
    assert "key1" in res and res["key1"] == "val1"
    assert "key2" in res and res["key2"] == "val2"


def test_parse_chart_no_extra_info():
    res = _parse_extra_info("")
    assert len(res) == 0
