# Changelog

Based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), following [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [Unreleased]

- breaking change: all App CR related functions and fixtures that require information about the Catalog
  the App references need now also a new `catalog_namespace` parameter

## [0.5.3]

- add support for Catalog CR from Giant Swarm App Platform
- mark AppCatalog CR related functions and classes as deprecated

## [0.5.2]

- fix docstring formatting
- make `get_app_catalog_object` function public

## [0.5.1]

- added: a couple of extracted helper methods to use outside of `pytest`'s fixture mechanism:
  - `create_app`
  - `delete_app`
  - `wait_for_app_to_be_deleted`
- unified imports to absolute paths

## [0.5.0]

- fix: `wait_for_deployments_to_run` needs to check for `availablePods` as well
- added: `namespace_factory` fixture you can use to create test time only namespaces
- change: `app_factory` takes now one more kwarg `deployment_namespace`, which configures
  the target deployment namespace for the created App CR; in other words, the `namespace` where the App
  CR is created can be now different than the `deployment_namespace` where app's components are deployed
- change: if the namespace passed as `namespace` argument to `app_factory` doesn't exist, it is automatically
  created using the new `namespace_factory` fixture

## [0.4.1]

- fix: work-around a bug in depended lib that was making `wait_for_deployments_to_run` fail

## [0.4.0]

- change: `app_factory_func` now checks if the passed App deploys successfully. This is configured using
  the `timeout_sec` argument, which by default is equal 60. Use value 0 to disable checking if App deploys OK.
- added:
  - `wait_for_apps_to_run` helper method
  - `wait_for_daemon_sets_to_run` helper method
  - `kubectl` method in `kube_cluster`, which allows you to make any calls using the binary `kubectl`
  - `random_namespace` fixture that creates a temporary namespace with a random name

## [0.3.2]

- added: support for `namespacedConfig` for App CR (`app_factory_func` fixture)

## [0.3.1]

- Remove any reference related to supporting multiple clusters. From now on this project always expects to get
  a `kube.config` for an already existing cluster.

## [0.2.1]
- added: include python 3.9 as a version for test running
- changed: updated dependencies
- removed: redundant code that was accepted in pykube-ng lib

## [0.1.10]
- added: more functions to help with handling namespaces, jobs and stateful sets.

## [0.1.9]
- fix: Don't supply `port` from kwargs to requests in `util.proxy_http_request`

## [0.1.8]
- change: use loadtest app helm chart 0.2.0

## [0.1.7]
- fix: type definitions for `wait_for_namespaced_object_condition function`

## [0.1.6]
- fix: fix the `chart_extra_info` fixture and add an example showing how to use it.

## [0.1.5]
- add: `--chart-extra-info` CLI option that can be used to pass arbitrary `key=value` maps to the test cases.
  Values fo the map are accessible in code as `chart_extra_info` fixture.

## [0.1.4]
- fix: wait_for_namespaced_objects_conditions was exiting prematurely when the objects were not yet present

## [0.1.3]
- fix plugin layout - import of fixtures
- fix the gatling fixture
- add more helper methods
  - wait for job / deployment
  - api proxy access

## [0.1.2] 2020-07-07
- no code changes
- tools include pre-commit

## [0.1.1] 2020-07-06
- First release version

## [0.1.0] 2020-05-03
- Initial commit
