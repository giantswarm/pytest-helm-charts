from typing import Optional

import pykube

from pytest_helm_charts.utils import inject_extra


def make_namespace_object(
    kube_client: pykube.HTTPClient,
    namespace_name: str,
    extra_metadata: Optional[dict] = None,
    extra_spec: Optional[dict] = None,
) -> pykube.Namespace:
    obj = inject_extra(
        {
            "apiVersion": "v1",
            "kind": "Namespace",
            "metadata": {
                "name": namespace_name,
            },
        },
        extra_metadata,
        extra_spec,
    )
    return pykube.Namespace(kube_client, obj)


def ensure_namespace_exists(
    kube_client: pykube.HTTPClient,
    namespace_name: str,
    extra_metadata: Optional[dict] = None,
    extra_spec: Optional[dict] = None,
) -> pykube.Namespace:
    """
    Checks if the Namespace exists and creates it if it doesn't
    Args:
        kube_client: client to use to connect to the k8s cluster
        namespace_name: a name of the Namespace to ensure
        extra_metadata: optional dict that will be merged with the 'metadata:' section of the object
        extra_spec: optional dict that will be merged with the 'spec:' section of the object

    Returns:
        Namespace resource object

    """
    ns = pykube.Namespace.objects(kube_client).get_or_none(name=namespace_name)
    if ns is None:
        ns = make_namespace_object(kube_client, namespace_name, extra_metadata, extra_spec)
        ns.create()
    return ns