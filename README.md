# pytest-helm-charts

[![build](https://github.com/giantswarm/pytest-helm-charts/workflows/build/badge.svg)](https://github.com/giantswarm/pytest-helm-charts/workflows/build/badge.svg)
[![codecov](https://codecov.io/gh/giantswarm/pytest-helm-charts/branch/master/graph/badge.svg)](https://codecov.io/gh/giantswarm/pytest-helm-charts)
[![Documentation Status](https://readthedocs.org/projects/pytest-helm-charts/badge/?version=latest)](https://pytest-helm-charts.readthedocs.io/en/latest/?badge=latest)
[![PyPI Version](https://img.shields.io/pypi/v/pytest-helm-charts.svg)](https://pypi.org/project/pytest-helm-charts/)
[![Python Versions](https://img.shields.io/pypi/pyversions/pytest-helm-charts.svg)](https://pypi.org/project/pytest-helm-charts/)
[![Apache License](https://img.shields.io/badge/license-apache-blue.svg)](https://pypi.org/project/pytest-helm-charts/)

A plugin to test helm charts on Kubernetes clusters.

Full documentation (including API) available on <https://pytest-helm-charts.readthedocs.io/>.

---

## Features

This plugin provides a set of [pytest](https://docs.pytest.org/) fixtures that allow you to easily
write tests for Helm charts and run them on Kubernetes clusters.

It can be also used to test Helm charts deployed using the Open Source
[Giant Swarm App Platform](https://docs.giantswarm.io/basics/app-platform/).

Most important features:

- provides [pykube-ng](http://pykube.readthedocs.io/) interface to access Kubernetes clusters
- provides [environment variables based options](#usage) to configure the target cluster to run on
- provides fixtures to work with some standard Kubernetes resources as well as some custom ones:
  - [Kubernetes objects](pytest_helm_charts.k8s)
  - [Giant Swarm App Platform objects](pytest_helm_charts.giantswarm_app_platform)
  - [Flux CD objects](pytest_helm_charts.flux)
- provides set of fixtures to easily work with Helm charts

## Requirements

Please check `[tool.poetry.dependencies]` list in the [`pyproject.toml`](pyproject.toml) file.

## Installation

You can install "pytest-helm-charts" via `pip` from `PyPI`:

```bash
pip install pytest-helm-charts
```

## Usage

### Running your tests

When you want to run your tests, you invoke `pytest` as usual, just configuring
cluster and chart information using environment variables or command line options.
The following options are available as environment variables (start `pytest` with `-h`
to check corresponding command line options):

- "KUBECONFIG" - (mandatory) a path to kube config file used to connect to a k8s cluster
- "ATS_CHART_PATH" - path to a chart being tested (if a chart is tested)
- "ATS_CHART_VERSION" - version of the chart being tested (if a chart is tested)
- "ATS_CLUSTER_TYPE" - type of the cluster used for testing
- "ATS_CLUSTER_VERSION" - k8s version of the cluster used for testing
- "ATS_APP_CONFIG_FILE_PATH" - optional path to a `values.yaml` file used to configure a chart under test
(if a chart is tested)
- "ATS_EXTRA_*" - any such arbitrary variable value will be extracted and included in the `test_extra_info` fixture

Currently, the only supported cluster type is `external`, which means the cluster is not
managed by the test suite. You just point the test suite to a `kube.config` file,
which can be used to connect to the Kubernetes API with `KUBECONFIG` env variable
option. For creating development time clusters, we recommend using
[KinD](https://kind.sigs.k8s.io/).

If you use this project to test Helm charts against Giant Swarm App Platform, the `existing`
cluster must already have the platform components installed. Please refer to and use
the [`app-test-suite`](https://github.com/giantswarm/app-test-suite) tool to easily
create `KinD` based clusters with all the components already installed.

### Writing tests

The easiest way to get started is by checking our
[examples](https://pytest-helm-charts.readthedocs.io/en/latest/examples/basic).

The list of available fixtures can be found by running `pytest --fixtures`, but
you can also just check [the most important fixtures](docs/fixtures.md).

Full [API docs](https://pytest-helm-charts.readthedocs.io/en/latest/api/pytest_helm_charts/)
are also available.

## Contributing

Contributions are very welcome.

- Project is managed with [`poetry`](https://python-poetry.org/),
  to start developing run `poetry install`
- Tests for all supported python versions can be run with [`tox`](https://tox.readthedocs.io/):
  `poetry run tox -- --log-cli-level info tests/`
- Please ensure
  [the coverage](https://codecov.io/gh/giantswarm/pytest-helm-charts/)
  at least stays the same before you submit a pull request.

## License

See [LICENSE](LICENSE).

## Changelog

See [CHANGELOG.md](CHANGELOG.md).

## Issues

If you encounter any problems, please [file an issue](https://github.com/giantswarm/pytest-helm-charts/issues)
along with a detailed description.
