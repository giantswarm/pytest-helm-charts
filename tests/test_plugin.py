from typing import Dict, Mapping

import pytest

from pytest_helm_charts.fixtures import _filter_extra_info_from_mapping, ATS_EXTRA_PREFIX


@pytest.mark.parametrize(["env", "expected"],
                         [
                             ({}, {}),
                             ({"t": "a"}, {}),
                             ({ATS_EXTRA_PREFIX+"TEST": "abc"}, {"test": "abc"}),
                             ({
                                 ATS_EXTRA_PREFIX+"CHUCK": "Norris",
                                 "Bruce": "Lee"
                             },
                              {"chuck": "Norris"})
                         ],
                         ids=["empty", "none matching", "single and matching", "some matching"])
def test_test_extra_info(env: Mapping[str, str], expected: Dict[str, str]) -> None:
    assert _filter_extra_info_from_mapping(env) == expected
