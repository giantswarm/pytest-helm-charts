from typing import Any, ClassVar, Optional

from pykube import HTTPClient
from pykube.query import Query

def __getattr__(name: str) -> Any: ...  # incomplete

class ObjectManager:
    def __getattr__(self, name: str) -> Any: ...  # incomplete
    def __call__(self, api: Any, namespace: Optional[Any] = None) -> Query: ...

class APIObject:
    objects: ClassVar[ObjectManager]
    def __init__(self, api: HTTPClient, obj: dict) -> None: ...
    def __getattr__(self, name: str) -> Any: ...  # incomplete

class NamespacedAPIObject(APIObject): ...
