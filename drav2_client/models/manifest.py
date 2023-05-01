from functools import cached_property
from typing import Any, ClassVar, Optional, TYPE_CHECKING
import warnings
from pydantic import BaseModel, Field, validator
from drav2_client.models.blob import Blob
from drav2_client.types import SHA256, MediaType

# To prevent circular import on runtime
if TYPE_CHECKING:
    from drav2_client.client import RegistryClient
    from drav2_client.models.response import RegistryResponse

__all__: list[str] = [
    "ManifestV1",
    "Layer",
    "Config",
    "ManifestV2",
    "FsLayer",
    "HistoryItem",
    "Jwk",
    "Header",
    "Signature",
]


class Config(BaseModel):
    media_type: Optional[MediaType] = Field(None, alias="mediaType")
    size: Optional[int] = None
    digest: Optional[SHA256] = None

    @validator("digest", pre=True)
    def validate_digest(cls, value: str | None) -> SHA256:
        if value is not None:
            value = SHA256(value)
            value.raise_for_validation()

        return value

    @validator("*")
    def force_default(cls, value: Any, values: dict[str, Any], **kwargs: Any) -> Any:
        if value is None:
            return kwargs["field"].default

        return value


class Layer(BaseModel):
    media_type: Optional[MediaType] = Field(None, alias="mediaType")
    size: Optional[int] = None
    digest: Optional[SHA256] = None
    _name: Optional[str] = ""
    _client: Optional["RegistryClient"] = None

    def get_blob(self, stream: bool = True) -> "RegistryResponse[Blob]":
        return self._client.get_blob(self._name, self.digest, stream=stream)

    @validator("digest", pre=True)
    def validate_digest(cls, value: str | None) -> SHA256:
        if value is not None:
            value = SHA256(value)
            value.raise_for_validation()

        return value

    @validator("*")
    def force_default(cls, value: Any, values: dict[str, Any], **kwargs: Any) -> Any:
        if value is None:
            return kwargs["field"].default

        return value

    class Config:
        underscore_attrs_are_private: bool = True


class ManifestV2(BaseModel):
    schema_version: Optional[int] = Field(None, alias="schemaVersion")
    media_type: Optional[MediaType] = Field(None, alias="mediaType")
    config: Optional[Config] = None
    layers: Optional[list[Layer]] = Field([])

    @cached_property
    def total_size(self) -> int:
        return sum(layer.size for layer in self.layers)

    @validator("*")
    def force_default(cls, value: Any, values: dict[str, Any], **kwargs: Any) -> Any:
        if value is None:
            return kwargs["field"].default

        return value

    class Config:
        # Must be defined to prevent TypeError exception when using cached_property
        keep_untouched: ClassVar[tuple[type[Any]]] = (cached_property,)


class FsLayer(BaseModel):
    blob_sum: Optional[SHA256] = Field("", alias="blobSum")
    _name: Optional[str] = ""
    _client: Optional["RegistryClient"] = None

    def get_blob(self, stream: bool = True) -> "RegistryResponse[Blob]":
        return self._client.get_blob(self._name, self.blob_sum, stream=stream)

    @validator("*")
    def force_default(cls, value: Any, values: dict[str, Any], **kwargs: Any) -> Any:
        if value is None:
            return kwargs["field"].default

        return value

    class Config:
        underscore_attrs_are_private: bool = True


class HistoryItem(BaseModel):
    v1_compatibility: Optional[str] = Field("", alias="v1Compatibility")

    @validator("*")
    def force_default(cls, value: Any, values: dict[str, Any], **kwargs: Any) -> Any:
        if value is None:
            return kwargs["field"].default

        return value


class Jwk(BaseModel):
    crv: Optional[str] = ""
    kid: Optional[str] = ""
    kty: Optional[str] = ""
    x: Optional[str] = ""
    y: Optional[str] = ""

    @validator("*")
    def force_default(cls, value: Any, values: dict[str, Any], **kwargs: Any) -> Any:
        if value is None:
            return kwargs["field"].default

        return value


class Header(BaseModel):
    jwk: Optional[Jwk] = None
    alg: Optional[str] = ""

    @validator("*")
    def force_default(cls, value: Any, values: dict[str, Any], **kwargs: Any) -> Any:
        if value is None:
            return kwargs["field"].default

        return value


class Signature(BaseModel):
    header: Optional[Header] = None
    signature: Optional[str] = ""
    protected: Optional[str] = ""

    @validator("*")
    def force_default(cls, value: Any, values: dict[str, Any], **kwargs: Any) -> Any:
        if value is None:
            return kwargs["field"].default

        return value


class ManifestV1(BaseModel):
    def __init__(__pydantic_self__, **data: Any) -> None:
        warnings.warn(
            "Manifest schema 1 should not be used for purposes "
            "other than backward compatibility. "
            "See https://docs.docker.com/registry/spec/manifest-v2-1/ to learn more.",
            DeprecationWarning,
        )
        super().__init__(**data)

    schema_version: Optional[int] = Field(None, alias="schemaVersion")
    name: Optional[str] = ""
    tag: Optional[str] = ""
    architecture: Optional[str] = ""
    fs_layers: Optional[list[FsLayer]] = Field([], alias="fsLayers")
    history: Optional[list[HistoryItem]] = Field([])
    signatures: Optional[list[Signature]] = Field([])

    @validator("*")
    def force_default(cls, value: Any, values: dict[str, Any], **kwargs: Any) -> Any:
        if value is None:
            return kwargs["field"].default

        return value
