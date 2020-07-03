# Most important fixtures included

The current list of all available fixtures can be found by running `pytest --fixtures`.

The most important list is included below.

## Generic fixture

![mkapi](pytest_helm_charts.fixtures.kube_cluster)

## Giant Swarm App Platform

![mkapi](pytest_helm_charts.giantswarm_app_platform.fixtures.app_factory)
![mkapi](pytest_helm_charts.giantswarm_app_platform.fixtures.app_catalog_factory)

## Applications useful for testing

We provide fixtures delivering some applications that might be useful for testing
apps, like load generators or simple test apps. They are deployed using 
[Giant Swarm App Platform fixtures](#giant-swarm-app-platform).

### HTTP testing

![mkapi](pytest_helm_charts.giantswarm_app_platform.apps.http_testing.gatling_app_factory)
![mkapi](pytest_helm_charts.giantswarm_app_platform.apps.http_testing.stormforger_load_app_factory)
