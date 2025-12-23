import shutil
import subprocess  # nosec
import unittest.mock
from typing import cast, List

import pytest
from _pytest.fixtures import FixtureRequest
from pytest_mock import MockFixture, MockerFixture

from pytest_helm_charts.clusters import ExistingCluster


def patch_for_construction(mocker: MockFixture) -> None:
    mocker.patch("pytest_helm_charts.clusters.KubeConfig.from_file", autospec=True)
    mocker.patch("pytest_helm_charts.clusters.HTTPClient")


def test_create_existing(mocker: MockFixture) -> None:
    kube_config_path = "/fake/path/kube.config"
    patch_for_construction(mocker)

    cluster = ExistingCluster(kube_config_path)
    client = cluster.create()

    assert client is not None
    assert cluster.kube_config_path == kube_config_path


def test_destroy_existing(mocker: MockFixture) -> None:
    kube_config_path = "/fake/path/kube.config"
    mocker.patch("pytest_helm_charts.clusters.KubeConfig.from_file", autospec=True)
    mocker.patch("pytest_helm_charts.clusters.HTTPClient")

    cluster = ExistingCluster(kube_config_path)
    client = cluster.create()
    cluster.destroy()

    client.session.close.assert_called_once()


def load_text_file(file_name: str) -> str:
    with open(file_name, "r") as f:
        return f.read()


@pytest.mark.parametrize(
    "cmd,file_name,expected_pods",
    [
        # test get multiple pods and if they are returned as a list
        (
            ["get", "pods"],
            "tests/resources/get_pods_result.json",
            [
                "app-operator-unique-647f46968b-wbn4h",
                "chart-operator-unique-86c9cbc86-l9xdj",
                "chartmuseum-chartmuseum-84b95cb77-kkg4x",
            ],
        ),
        # test get a single pod and if it is returned as an object
        (["get", "pod"], "tests/resources/get_pod_result.json", ["app-operator-unique-647f46968b-wbn4h"]),
    ],
)
def test_kubectl_in_existing(cmd: List[str], file_name: str, expected_pods: List[str], request: FixtureRequest) -> None:
    kube_config_path = "/fake/path/kube.config"
    mocker = request.getfixturevalue("mocker")
    patch_for_construction(mocker)
    mocker.patch("shutil.which")
    mocker.patch("subprocess.check_output")
    cast(unittest.mock.Mock, subprocess.check_output).return_value = load_text_file(file_name)

    cluster = ExistingCluster(kube_config_path)
    cluster.create()
    res = cluster.kubectl(" ".join(cmd))

    cast(unittest.mock.Mock, shutil.which).assert_called_once_with("kubectl")
    expected_args = ["kubectl", *cmd, f"--kubeconfig={kube_config_path}", "--output=json"]
    assert sorted(cast(unittest.mock.Mock, subprocess.check_output).call_args.args[0]) == sorted(expected_args)
    if isinstance(res, list):
        assert len(res) == len(expected_pods)
        pod_names = [p["metadata"]["name"] for p in res]
    else:
        pod_names = [res["metadata"]["name"]]
    assert set(pod_names) == set(expected_pods)


@pytest.mark.parametrize(
    "cmd,expected_string,expected_exit_code,use_shell",
    [
        # test correctly annotate pod
        ("annotate pod testpod a=b", "pod/testpod labeled", 0, False),
        # test annotate non-existing pod
        ("annotate pod testpod a=b", 'Error from server (NotFound): pods "testpod" not found', 1, False),
        # test delete pod
        ("delete pod testpod", 'pod "testpod" deleted', 0, True),
        # test delete non-existing pod
        ("delete pod testpod", 'Error from server (NotFound): pods "testpod" not found', 1, True),
    ],
)
def test_non_json_kubectl_in_existing(
    cmd: str, expected_string: str, expected_exit_code: int, use_shell: bool, request: FixtureRequest
) -> None:
    kube_config_path = "/fake/path/kube.config"
    mocker: MockerFixture = request.getfixturevalue("mocker")
    patch_for_construction(mocker)
    mocker.patch("shutil.which")
    mocker.patch("subprocess.check_output")
    if expected_exit_code == 0:
        cast(unittest.mock.Mock, subprocess.check_output).return_value = expected_string
    else:
        cast(unittest.mock.Mock, subprocess.check_output).side_effect = subprocess.CalledProcessError(
            expected_exit_code, cmd, "", expected_string
        )

    cluster = ExistingCluster(kube_config_path)
    cluster.create()
    if expected_exit_code == 0:
        res = cluster.kubectl(cmd, output="", use_shell=use_shell)
        assert res == expected_string
    else:
        with pytest.raises(subprocess.CalledProcessError) as err_info:
            cluster.kubectl(cmd, output="", use_shell=use_shell)
        assert err_info.value.returncode == expected_exit_code
        assert err_info.value.stderr == expected_string

    cast(unittest.mock.Mock, shutil.which).assert_called_once_with("kubectl")
    expected_args = (
        f"kubectl {cmd} --kubeconfig={kube_config_path}"
        if use_shell
        else ["kubectl"] + cmd.split() + [f"--kubeconfig={kube_config_path}"]
    )

    cast(unittest.mock.Mock, subprocess.check_output).assert_called_once_with(
        expected_args,
        encoding="utf-8",
        input="",
        shell=use_shell,
        stderr=-1,  # nosec
    )
