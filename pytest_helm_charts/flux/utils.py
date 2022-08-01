import abc
import logging

from pykube.objects import NamespacedAPIObject

logger = logging.getLogger(__name__)

FLUX_CR_READY_TIMEOUT_SEC = 30


class NamespacedFluxCR(NamespacedAPIObject, abc.ABC):
    pass


def flux_cr_ready(flux_obj: NamespacedFluxCR) -> bool:
    has_conditions = "status" in flux_obj.obj and "conditions" in flux_obj.obj["status"]
    if not has_conditions:
        return False
    conditions_count = len(flux_obj.obj["status"]["conditions"])
    if conditions_count == 0:
        return False
    if conditions_count > 1:
        logging.warning(
            f"Found '{conditions_count}' status conditions when expecting just 1. Using only"
            f" the first one on the list."
        )
    condition = flux_obj.obj["status"]["conditions"][0]
    return condition["type"] == "Ready" and condition["status"] == "True"
