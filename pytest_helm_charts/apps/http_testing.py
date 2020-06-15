from typing import Callable, Dict, Iterable, List

import pytest
from pykube import HTTPClient, ConfigMap

from pytest_helm_charts.apps.app_catalog import AppCR, AppCatalogFactoryFunc
from pytest_helm_charts.apps.deployment import AppFactoryFunc, YamlDict

StormforgerLoadAppFactoryFunc = Callable[[int, str, Dict[str, str]], AppCR]


@pytest.fixture(scope="module")
def stormforger_load_app_factory(kube_client: HTTPClient,
                                 app_catalog_factory: AppCatalogFactoryFunc,
                                 app_factory: AppFactoryFunc) -> StormforgerLoadAppFactoryFunc:
    def _stormforger_load_app_factory(replicas: int, host_url: str,
                                      node_affinity_selector: Dict[str, str] = None) -> AppCR:
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


GatlingAppFactoryFunc = Callable[[str, Dict[str, str]], AppCR]


@pytest.fixture(scope="module")
def gatling_app_factory(kube_client: HTTPClient,
                        app_catalog_factory: AppCatalogFactoryFunc,
                        app_factory: AppFactoryFunc) -> Iterable[GatlingAppFactoryFunc]:
    created_configmaps: List[ConfigMap] = []

    def _gatling_app_factory(simulation_file: str,
                             node_affinity_selector: Dict[str, str] = None) -> AppCR:
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
