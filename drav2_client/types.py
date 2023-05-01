import enum
import re
from typing import Any, ClassVar, NewType, TypeVar

from pydantic import BaseModel

__all__: list[str] = [
    "AnyTransport",
    "MediaType",
    "SHA256",
]

AnyTransport: Any = Any
T = TypeVar("T", bound=BaseModel)


class MediaType(str, enum.Enum):
    SIGNED_MANIFEST_V1 = "application/vnd.docker.distribution.manifest.v1+prettyjws"
    MANIFEST_V1 = "application/vnd.docker.distribution.manifest.v1+json"
    MANIFEST_V2 = "application/vnd.docker.distribution.manifest.v2+json"
    MANIFEST_LIST = "application/vnd.docker.distribution.manifest.list.v2+json"
    CONTAINER_CONFIG = "application/vnd.docker.container.image.v1+json"
    LAYER = "application/vnd.docker.image.rootfs.diff.tar.gzip"
    FOREIGN_LAYER = "application/vnd.docker.image.rootfs.foreign.diff.tar.gzip"  # Should never be pushed
    PLUGIN_CONFIG = "application/vnd.docker.plugin.v1+json"


class SHA256(str):
    _SHA256_PATTERN: ClassVar[re.Pattern] = re.compile(r"sha256:[a-f\d]{64}")

    def raise_for_validation(self) -> None:
        if not self._SHA256_PATTERN.match(self.lower()):
            raise ValueError(
                f"The SHA256 hash should follow the "
                f"pattern {self._SHA256_PATTERN.pattern}"
            )
