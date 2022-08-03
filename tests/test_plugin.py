from typing import Dict, Mapping

import pytest

from pytest_helm_charts.fixtures import _filter_extra_info_from_mapping, ENV_VAR_ATS_EXTRA_PREFIX


@pytest.mark.parametrize(
    ["env", "expected"],
    [
        ({}, {}),
        ({"t": "a"}, {}),
        ({ENV_VAR_ATS_EXTRA_PREFIX + "TEST": "abc"}, {"test": "abc"}),
        ({ENV_VAR_ATS_EXTRA_PREFIX + "CHUCK": "Norris", "Bruce": "Lee"}, {"chuck": "Norris"}),
    ],
    ids=["empty", "none matching", "single and matching", "some matching"],
)
def test_test_extra_info(env: Mapping[str, str], expected: Dict[str, str]) -> None:
    assert _filter_extra_info_from_mapping(env) == expected
