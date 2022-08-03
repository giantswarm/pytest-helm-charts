# Changelog

Based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), following [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.7.1] - 2022.08.03

- changed:
  - `_flux_cr_ready` made public by renaming to `flux_cr_ready`
  - Test information data is now primarily being input by (partially mandatory) environment variables.
    Majority of old command line parameters should still work, but environment variables usage is encouraged.
    This allows `pytest-helm-charts` to be easily used without the `app-test-suite`
    project, which was enforcing the cmd line parameters before. The following env vars are recognised and used in
    fixtures (when requested):
    - "KUBECONFIG" - (mandatory) a path to kube config file used to connect to a k8s cluster
    - "ATS_CHART_PATH" - path to a chart being tested (if a chart is tested)
    - "ATS_CHART_VERSION" - version of the chart being tested (if a chart is tested)
    - "ATS_CLUSTER_TYPE" - (informative only) type of the cluster used for testing
    - "ATS_CLUSTER_VERSION" - (informative only) k8s version of the cluster used for testing
    - "ATS_APP_CONFIG_FILE_PATH" - optional path to a `values.yaml` file used to configure a chart under test
      (if a chart is tested)
    - "ATS_EXTRA_*" - any such arbitrary variable value will be extracted and included in the `test_extra_info` fixture
  - `chart_extra_info` fixture was removed, as the more general `test_extra_info` is available

- updated:
  - `pytest` upgraded from 6.x series to 7.x

## [0.7.1]

- fixed:
  - 'repositories' attribute of Catalog CR is now handled

## [0.7.0]

- changed:
  - all the changes from beta releases below
  - fixed docs issues

## [0.7.0-beta.2]

- changed:
  - rename 'api' module to 'k8s'
  - update Kustomization to v1beta2
- fixed:
  - in HelmRelease, ensure 'targetNamespace' if it doesn't exist
  - logging level adjusted (debug only if no errors) and added consistent log messages about creating and deleting resources
  - add missing imports in plugin.py

## [0.7.0-beta.1]

- added:
  - all kubernetes API Objects targeting fixtures have now a function scoped counterpart named `*_function_scope`
  - package `flux` was added to deal with Flux CRs
- changed:
  - all fixture factories that create objects and delete them after they are out of scope, now
    actively wait for the object to be gone. Previously, only `delete()` request was sent without
    checking if the object is gone, which was causing a bunch of race conditions between test runs.
  - All recursively-required missing resources are now automatically created. This usually means
    that if the `Namespace` you want to put your resource in doesn't exist, it will be created
    automatically for you. The same applies to `App` and the required `Catalog`.
  - switch from `Callable` to `Protocol` for factory types (much better type hinting)
  - all functions making API objects take now optional `extra_metadata` and `extra_spec` arguments,
    which are merged with object definitions without any restrictions nor validation
  - `wait_for_apps_to_run` accepts now a new parameter `fail_fast: bool = False`; when it's `True` and the App's
    status ever reaches `failed`, the wait fails as well, without waiting for subsequent state changes.
  - cleanups:
    - all methods creating objects, but not submitting them to k8s API, match now `make-*-object` pattern
    - `HTTPClient` connection object is always the first method parameter
    - removed the `namespaceConfig*` arguments of `make_app_object`, as they can be now included
      using the `extra-*` args
    - multiple classes were moved across modules and packages to match the following rules:
      - every Resource / CustomResource is a single module
      - groups of API Resources (like giant swarm app platform or flux - in the future) go to packages
    - `wait_for_namespaced_objects_condition` function is renamed to `wait_for_objects_condition` as it now supports
      both cluster-scope and namespace-scope resources. Additionally, it allows now to pass a function for checking for
      fail fast conditions in objects awaited.
- fixed:
  - namespaces requested from `namespace_factory*` fixtures are now deleted only if they were created by the fixture
    (and not already existing in the cluster)

## [0.6.0]

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

- fix: work-around a bug in a depended lib that was making `wait_for_deployments_to_run` fail

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
