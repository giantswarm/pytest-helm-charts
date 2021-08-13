from typing import NamedTuple, Optional

from pykube import ConfigMap

from pytest_helm_charts.giantswarm_app_platform.custom_resources import AppCR


class ConfiguredApp(NamedTuple):
    app: AppCR
    app_cm: Optional[ConfigMap]