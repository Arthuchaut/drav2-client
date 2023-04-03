import enum
from typing import Any

__all__: list[str] = [
    "AnyTransport",
    "ManifestMediaType",
]

AnyTransport: Any = Any


class ManifestMediaType(str, enum.Enum):
    V1 = "application/vnd.docker.distribution.manifest.v1+prettyjws"
    V2 = "application/vnd.docker.distribution.manifest.v2+json"
