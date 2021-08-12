from typing import NamedTuple, Optional

from pykube import ConfigMap

from .custom_resources import AppCR


class ConfiguredApp(NamedTuple):
    app: AppCR
    app_cm: Optional[ConfigMap]
