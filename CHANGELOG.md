# Changelog

Based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), following [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [Unreleased]

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
