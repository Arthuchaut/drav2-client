import enum
from typing import Any

__all__: list[str] = [
    "AnyTransport",
    "MediaType",
]

AnyTransport: Any = Any


class MediaType(str, enum.Enum):
    SIGNED_MANIFEST_V1 = "application/vnd.docker.distribution.manifest.v1+prettyjws"
    MANIFEST_V1 = "application/vnd.docker.distribution.manifest.v1+json"
    MANIFEST_V2 = "application/vnd.docker.distribution.manifest.v2+json"
    MANIFEST_LIST = "application/vnd.docker.distribution.manifest.list.v2+json"
    CONTAINER_CONFIG = "application/vnd.docker.container.image.v1+json"
    LAYER = "application/vnd.docker.image.rootfs.diff.tar.gzip"
    FOREIGN_LAYER = "application/vnd.docker.image.rootfs.foreign.diff.tar.gzip"  # “Layer”, as a gzipped tar that should never be pushed
    PLUGIN_CONFIG = "application/vnd.docker.plugin.v1+json"
