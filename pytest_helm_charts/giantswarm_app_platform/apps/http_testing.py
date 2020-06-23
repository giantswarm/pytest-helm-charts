"""This modules contains apps useful for testing HTTP applications."""
from typing import Callable, Dict, Iterable, List, Optional

import pytest
from pykube import HTTPClient, ConfigMap

from pytest_helm_charts.giantswarm_app_platform.custom_resources import AppCR
from pytest_helm_charts.giantswarm_app_platform.app import AppFactoryFunc
from pytest_helm_charts.utils import YamlDict

StormforgerLoadAppFactoryFunc = Callable[[int, str, Optional[Dict[str, str]]], AppCR]


@pytest.fixture(scope="module")
def stormforger_load_app_factory(app_factory: AppFactoryFunc) -> StormforgerLoadAppFactoryFunc:
    """A factory fixture to return a function that can produce Stromforger Load App instances.

    Args:
        app_factory: auto-injected [app_factory](..app.app_factory) fixture.

    Returns:
        A function you can use to create stormforger instances. The function has the following args.

    Examples:
        Create and run using 8 replicas erving the 'loadtest.local' URL. Use affinity selector to run
        on the 'localhost' Kubernetes Node.

        >>> stormforger_load_app_factory(8, "loadtest.local", {"kubernetes.io/hostname": "localhost"})
    """
    def _stormforger_load_app_factory(replicas: int, host_url: str,
                                      node_affinity_selector: Optional[Dict[str, str]] = None) -> AppCR:
        """Creates and deploys stormforger load app by creating the relevant App CR in the API.

        Args:
            replicas: number of replicas of Pods the app should run.
            host_url: the URL under which the app will serve requests.
            node_affinity_selector: option node affinity Kubernetes selector. Default={default}.

        Returns:
            [AppCR](AppCR) describing the CR created in API.

        """
        config_values: YamlDict = {
            "replicaCount": replicas,
            "ingress": {
                "enabled": "true",
                "annotations": {
                    "kubernetes.io/ingress.class": "nginx"
                },
                "paths": [
                    "/"
                ],
                "hosts": [
                    host_url
                ]
            },
            "autoscaling": {
                "enabled": "false"
            }
        }

        if node_affinity_selector is not None:
            config_values["nodeAffinity"] = {
                "enabled": "true",
                "selector": node_affinity_selector
            }
        stormforger_app = app_factory("loadtest-app", "0.1.2", "default",
                                      "https://giantswarm.github.io/default-catalog/",
                                      "default", config_values)
        return stormforger_app

    return _stormforger_load_app_factory


GatlingAppFactoryFunc = Callable[[str, Optional[Dict[str, str]]], AppCR]


@pytest.fixture(scope="module")
def gatling_app_factory(kube_client: HTTPClient,
                        app_factory: AppFactoryFunc) -> Iterable[GatlingAppFactoryFunc]:
    created_configmaps: List[ConfigMap] = []

    def _gatling_app_factory(simulation_file: str,
                             node_affinity_selector: Optional[Dict[str, str]] = None) -> AppCR:
        namespace = "default"
        with open(simulation_file) as f:
            simulation_code = f.read()
        simulation_cm: YamlDict = {
            "apiVersion": "v1",
            "kind": "ConfigMap",
            "metadata": {
                "name": "gatling-simulation",
                "namespace": namespace,
                "labels": {
                    "app": "gatling"
                },
            },
            "data": {
                "NginxSimulation.scala": simulation_code,
            }
        }

        config_values: YamlDict = {
            "simulation": {
                "configMap": {
                    "name": simulation_cm["metadata"]["name"]
                },
                "name": "nginx.NginxSimulation",
            }
        }

        if node_affinity_selector is not None:
            config_values["nodeAffinity"] = {
                "enabled": "true",
                "selector": node_affinity_selector
            }

        simulation_cm_obj = ConfigMap(kube_client, simulation_cm)
        simulation_cm_obj.create()
        created_configmaps.append(simulation_cm_obj)
        gatling_app = app_factory("gatling-app", "1.0.2", "giantswarm-playground",
                                  "https://giantswarm.github.com/giantswarm-playground-catalog/",
                                  namespace, config_values)
        return gatling_app

    yield _gatling_app_factory

    for cm in created_configmaps:
        cm.delete()
