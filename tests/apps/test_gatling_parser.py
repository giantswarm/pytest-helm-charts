from pytest_helm_charts.giantswarm_app_platform.apps.http_testing import GatlingParser


def test_gatling_parser_good():
    text: str = ""
    with open("tests/apps/sample.log") as f:
        text = f.read()

    p = GatlingParser(text)
    assert p.max_response_time == 30
    assert p.mean_response_time == 3
    assert p.mean_rps == 200.0
    assert p.mean_rps == 200.0
    assert p.min_response_time == 1
    assert p.request_count_bad == 0
    assert p.request_count_ok == 400
    assert p.request_count_total == 400
    assert p.request_failure == 0.0
    assert p.request_success_ratio == 1.0
    assert p.response_time_50th_percentile == 3
    assert p.response_time_75th_percentile == 3
    assert p.response_time_95th_percentile == 5
    assert p.response_time_99th_percentile == 10


def test_gatling_parser_fail():
    text: str = ""
    with open("tests/apps/sample-fail.log") as f:
        text = f.read()

    p = GatlingParser(text)
    assert p.max_response_time == 60330
    assert p.mean_response_time == 852
    assert p.mean_rps == 3214.286
    assert p.min_response_time == 0
    assert p.request_count_bad == 431904
    assert p.request_count_ok == 18096
    assert p.request_count_total == 450000
    assert p.request_failure == 0.9597866666666667
    assert p.request_success_ratio == 0.04021333333333333
    assert p.response_time_50th_percentile == 398
    assert p.response_time_75th_percentile == 587
    assert p.response_time_95th_percentile == 3915
    assert p.response_time_99th_percentile == 6546
