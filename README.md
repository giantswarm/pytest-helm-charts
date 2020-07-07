[![build](https://github.com/giantswarm/pytest-helm-charts/workflows/build/badge.svg)](https://github.com/giantswarm/pytest-helm-charts/workflows/build/badge.svg)
[![codecov](https://codecov.io/gh/giantswarm/pytest-helm-charts/branch/master/graph/badge.svg)](https://codecov.io/gh/giantswarm/pytest-helm-charts)
[![Documentation Status](https://readthedocs.org/projects/pytest-helm-charts/badge/?version=latest)](https://pytest-helm-charts.readthedocs.io/en/latest/?badge=latest)
[![PyPI Version](https://img.shields.io/pypi/v/pytest-helm-charts.svg)](https://pypi.org/project/pytest-helm-charts/)
[![Python Versions](https://img.shields.io/pypi/pyversions/pytest-helm-charts.svg)](https://pypi.org/project/pytest-helm-charts/)
[![Apache License](https://img.shields.io/badge/license-apache-blue.svg)](https://pypi.org/project/pytest-helm-charts/)

# pytest-helm-charts

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
- provides [command line options](#usage) to configure the target cluster to run on
- supports custom resource for the Giant Swarm App Platform:
    - [App](https://docs.giantswarm.io/reference/cp-k8s-api/apps.application.giantswarm.io/)
    - [AppCatalog](https://docs.giantswarm.io/reference/cp-k8s-api/appcatalogs.application.giantswarm.io/)
- provides set of fixtures to easily work with Helm charts

## Requirements

- python 3.7+
- pytest 5.4.2+
- pykube-ng = 20.7.0+

## Installation

You can install "pytest-helm-charts" via `pip` from `PyPI`:

```
$ pip install pytest-helm-charts
```

## Usage

### Running your tests

When you want to run your tests, you invoke `pytest` as usual, just passing additional
flags on the command line. You can inspect them directly by running `pytest -h` and
checking the "helm-charts" section.

Currently, the only supported cluster type is `external`, which means the cluster is not
managed by the test suite. You just point the test suite to a `kube.config` file,
which can be used to connect to the Kubernetes API with `--kube-config` command line
option. For creating development time clusters, we recommend using
[KinD](https://kind.sigs.k8s.io/).

If you use this project to test Helm charts against Giant Swarm App Platform, the `existing`
cluster must already have the platform components installed. Please refer to and use
the [`kube-app-testing`](https://github.com/giantswarm/kube-app-testing) tool to easily
create KinD based clusters with all the components already installed.

### Writing tests

The easiest way to get started is by checking our
[examples](https://pytest-helm-charts.readthedocs.io/en/latest/examples/basic).

The list of available fixtures can be found by running `pytest --fixtures`, but
you can also just check [the most important fixtures](fixtures.md).

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

If you encounter any problems, please [file an issue](https://github.com/giantswarm/pytest-helm-charts/issues) along with a detailed description.
