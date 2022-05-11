"""This modules contains apps useful for testing HTTP applications."""
import math
from typing import Dict, Iterable, List, Optional, Protocol, Tuple

import pytest
from pykube import ConfigMap
from pytest_helm_charts.clusters import Cluster
from pytest_helm_charts.giantswarm_app_platform.app import AppFactoryFunc, ConfiguredApp
from pytest_helm_charts.utils import YamlDict, delete_and_wait_for_objects


class StormforgerLoadAppFactoryFunc(Protocol):
    def __call__(
        self,
        replicas: int,
        host_url: str,
        node_affinity_selector: Optional[Dict[str, str]] = None,
        extra_metadata: Optional[dict] = None,
        extra_spec: Optional[dict] = None,
    ) -> ConfiguredApp:
        ...


@pytest.fixture(scope="module")
def stormforger_load_app_factory(app_factory: AppFactoryFunc) -> StormforgerLoadAppFactoryFunc:
    """A factory fixture to return a function that can produce Stromforger Load App instances.
    Fixture's scope is 'module'..

    Args:
        app_factory: auto-injected [app_factory](pytest_helm_charts.giantswarm_app_platform.app.app_factory) fixture.

    Returns:
        A function you can use to create stormforger instances. The function has the following args.

    Examples:
        Create and run using 8 replicas erving the 'loadtest.local' URL. Use affinity selector to run
        on the 'localhost' Kubernetes Node.

        >>> stormforger_load_app_factory(8, "loadtest.local", {"kubernetes.io/hostname": "localhost"})
    """

    def _stormforger_load_app_factory(
        replicas: int,
        host_url: str,
        node_affinity_selector: Optional[Dict[str, str]] = None,
        extra_metadata: Optional[dict] = None,
        extra_spec: Optional[dict] = None,
    ) -> ConfiguredApp:
        """Creates and deploys stormforger load app by creating the relevant App CR in the API.

        Args:
            replicas: number of replicas of Pods the app should run.
            host_url: the URL under which the app will serve requests.
            node_affinity_selector: option node affinity Kubernetes selector. Default={default}.
             extra_metadata: optional dict that will be merged with the 'metadata:' section of the object
             extra_spec: optional dict that will be merged with the 'spec:' section of the object

        Returns:
            [AppCR](AppCR) describing the CR created in API.

        """
        config_values: YamlDict = {
            "replicaCount": replicas,
            "ingress": {
                "enabled": "true",
                "annotations": {"kubernetes.io/ingress.class": "nginx"},
                "paths": ["/"],
                "hosts": [host_url],
            },
            "autoscaling": {"enabled": "false"},
        }

        if node_affinity_selector is not None:
            config_values["nodeAffinity"] = {"enabled": "true", "selector": node_affinity_selector}
        stormforger_app = app_factory(
            "loadtest-app",
            "0.2.0",
            "default",
            "default",
            "https://giantswarm.github.io/default-catalog/",
            config_values=config_values,
            extra_metadata=extra_metadata,
            extra_spec=extra_spec,
        )
        return stormforger_app

    return _stormforger_load_app_factory


class GatlingAppFactoryFunc(Protocol):
    def __call__(
        self,
        simulation_file: str,
        node_affinity_selector: Optional[Dict[str, str]] = None,
        extra_metadata: Optional[dict] = None,
        extra_spec: Optional[dict] = None,
    ) -> ConfiguredApp:
        ...


@pytest.fixture(scope="module")
def gatling_app_factory(kube_cluster: Cluster, app_factory: AppFactoryFunc) -> Iterable[GatlingAppFactoryFunc]:
    """A factory fixture to return a function that can produce Gatling instances. Gatling is a HTTP
    performance testing tool. Fixture's scope is 'module'..

    Args:
        app_factory: auto-injected [app_factory](pytest_helm_charts.giantswarm_app_platform.app.app_factory) fixture.
        kube_cluster: auto-injected [kube_cluster](pytest_helm_charts.fixtures.kube_cluster) fixture.

    Returns:
        A function you can use to create Gatling instances.
    """

    created_configmaps: List[ConfigMap] = []

    def _gatling_app_factory(
        simulation_file: str,
        node_affinity_selector: Optional[Dict[str, str]] = None,
        extra_metadata: Optional[dict] = None,
        extra_spec: Optional[dict] = None,
    ) -> ConfiguredApp:
        namespace = "default"
        with open(simulation_file) as f:
            simulation_code = f.read()
        simulation_cm: YamlDict = {
            "apiVersion": "v1",
            "kind": "ConfigMap",
            "metadata": {"name": "gatling-simulation", "namespace": namespace, "labels": {"app": "gatling"}},
            "data": {"NginxSimulation.scala": simulation_code},
        }

        config_values: YamlDict = {
            "simulation": {"configMap": {"name": simulation_cm["metadata"]["name"]}, "name": "nginx.NginxSimulation"}
        }

        if node_affinity_selector is not None:
            config_values["nodeAffinity"] = {"enabled": "true", "selector": node_affinity_selector}

        simulation_cm_obj = ConfigMap(kube_cluster.kube_client, simulation_cm)
        simulation_cm_obj.create()
        created_configmaps.append(simulation_cm_obj)
        gatling_app = app_factory(
            "gatling-app",
            "1.0.2",
            "giantswarm-playground",
            "default",
            "https://giantswarm.github.io/giantswarm-playground-catalog/",
            namespace=namespace,
            config_values=config_values,
            extra_metadata=extra_metadata,
            extra_spec=extra_spec,
        )
        return gatling_app

    yield _gatling_app_factory

    delete_and_wait_for_objects(kube_cluster.kube_client, ConfigMap, created_configmaps)


class GatlingParser:
    def __init__(self, lines: str) -> None:
        split_lines = lines.splitlines()
        start_line_query = [i for i in range(len(split_lines)) if split_lines[i] == "Generating reports..."]
        assert len(start_line_query) == 1
        start_line = start_line_query[0]
        report_lines = split_lines[start_line + 2 : start_line + 20]
        assert report_lines[0] == "================================================================================"
        assert report_lines[1] == "---- Global Information --------------------------------------------------------"

        total, ok, bad = self.__parse_result_line(report_lines[2], "request count")
        self.request_count_total, self.request_count_ok, self.request_count_bad = int(total), int(ok), int(bad)
        self.request_success_ratio = float(self.request_count_ok) / float(self.request_count_total)
        self.request_failure = float(self.request_count_bad) / float(self.request_count_total)

        min_time, _, _ = self.__parse_result_line(report_lines[3], "min response time")
        self.min_response_time = int(min_time)

        max_time, _, _ = self.__parse_result_line(report_lines[4], "max response time")
        self.max_response_time = int(max_time)

        mean_time, _, _ = self.__parse_result_line(report_lines[5], "mean response time")
        self.mean_response_time = int(mean_time)

        std_deviation, _, _ = self.__parse_result_line(report_lines[6], "std deviation")
        self.std_deviation = int(std_deviation)

        response_time_50th_percentile, _, _ = self.__parse_result_line(report_lines[7], "response time 50th percentile")
        self.response_time_50th_percentile = int(response_time_50th_percentile)

        response_time_75th_percentile, _, _ = self.__parse_result_line(report_lines[8], "response time 75th percentile")
        self.response_time_75th_percentile = int(response_time_75th_percentile)

        response_time_95th_percentile, _, _ = self.__parse_result_line(report_lines[9], "response time 95th percentile")
        self.response_time_95th_percentile = int(response_time_95th_percentile)

        response_time_99th_percentile, _, _ = self.__parse_result_line(
            report_lines[10], "response time 99th percentile"
        )
        self.response_time_99th_percentile = int(response_time_99th_percentile)

        mean_rps, _, _ = self.__parse_result_line(report_lines[11], "mean requests/sec")
        self.mean_rps = float(mean_rps)

        assert report_lines[12] == "---- Response Time Distribution ------------------------------------------------"
        self.response_time_distribution: Dict[Tuple[float, float], int] = {}

        line = report_lines[13][2:]
        fields = list(filter(None, line.split(" ")))
        assert fields[0] == "t"
        upper = float(fields[2])
        self.response_time_distribution[(0, upper)] = int(fields[4])

        line = report_lines[14][2:]
        fields = list(filter(None, line.split(" ")))
        assert fields[3] == "t"
        lower = float(fields[0])
        upper = float(fields[5])
        self.response_time_distribution[(lower, upper)] = int(fields[7])

        line = report_lines[15][2:]
        fields = list(filter(None, line.split(" ")))
        assert fields[0] == "t"
        lower = float(fields[2])
        self.response_time_distribution[(lower, math.inf)] = int(fields[4])

        line = report_lines[16][2:]
        fields = list(filter(None, line.split(" ")))
        assert fields[0] == "failed"

    @staticmethod
    def __parse_result_line(line: str, header: str) -> Tuple[str, str, str]:
        assert line[0:2] == "> "
        line = line[2:]
        assert line.find(header) >= 0
        fields = line[len(header) :].split(" ")
        fields = list(filter(None, fields))
        total = fields[0]
        ok = fields[1].split("=")[1]
        bad = fields[2].split("=")[1].rstrip(")")
        return total, ok, bad
