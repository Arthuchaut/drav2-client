from functools import cached_property
from typing import Any, ClassVar, Literal, Optional, TYPE_CHECKING
import warnings
from pydantic import BaseModel, Field, validator
from drav2.models.blob import Blob
from drav2.models.errors import Error
from drav2.types import SHA256, MediaType

# To prevent circular import on runtime
if TYPE_CHECKING:  # pragma: no cover
    from drav2.client import RegistryClient
    from drav2.models.response import RegistryResponse

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
    """The ManifestV2 config field definition.

    Attributes:
        media_type (Optional): The content type of the config.
        size (Optional): The size of the config metadata.
        digest (Optional): The hashed content of the config metadata.
    """

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
    """The ManifestV2 layer field definition.

    Attributes:
        media_type (Optional): The content type of the layer.
        size (Optional): The size (in Bytes) of the blob.
        digest (Optional): The hashed content of the blob.
    """

    media_type: Optional[MediaType] = Field(None, alias="mediaType")
    size: Optional[int] = None
    digest: Optional[SHA256] = None
    _name: Optional[str] = ""
    _client: Optional["RegistryClient"] = None

    def get_blob(self, stream: bool = True) -> "RegistryResponse[Blob | Error]":
        """Get the blob of the layer.

        Args:
            stream (Optional): Enable or not the streaming mode for retrieving
                the binary data. This mode is strongly recommanded to prevent
                memory overflow. Default to True.

        Returns:
            RegistryResponse[Blob | Error]: The blob related to the layer.
        """

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
        underscore_attrs_are_private: ClassVar[Literal[True]] = True


class ManifestV2(BaseModel):
    """The manifest (version 2) model definition.

    Attributes:
        schema_version (Optional): The version of the schema (should be always 2).
        media_type (Optional): The content type of the manifest.
        config (Optional): Miscellaneous information about the manifest.
        layers (Optional): The layers that compose the image defined by the manifest.
        total_size (Property): The total size (in Bytes) of the whole layers.
    """

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
    """The layer field definition of the ManifestV1 model.

    Attributes:
        blob_sum (Optional): The hashed content of the blob.
    """

    blob_sum: Optional[SHA256] = Field("", alias="blobSum")
    _name: Optional[str] = ""
    _client: Optional["RegistryClient"] = None

    def get_blob(self, stream: bool = True) -> "RegistryResponse[Blob | Error]":
        """Get the blob of the layer.

        Args:
            stream (Optional): Enable or not the streaming mode for retrieving
                the binary data. This mode is strongly recommanded to prevent
                memory overflow. Default to True.

        Returns:
            RegistryResponse[Blob | Error]: The blob related to the layer.
        """

        return self._client.get_blob(self._name, self.blob_sum, stream=stream)

    @validator("*")
    def force_default(cls, value: Any, values: dict[str, Any], **kwargs: Any) -> Any:
        if value is None:
            return kwargs["field"].default

        return value

    class Config:
        underscore_attrs_are_private: ClassVar[Literal[True]] = True


class HistoryItem(BaseModel):
    """The image building statement history field of the ManifestV1 model.

    Note:
        The number of items should be equals to the number of layers.

    Attributes:
        v1_compatibility (Optional): The statement layer.
    """

    v1_compatibility: Optional[str] = Field("", alias="v1Compatibility")

    @validator("*")
    def force_default(cls, value: Any, values: dict[str, Any], **kwargs: Any) -> Any:
        if value is None:
            return kwargs["field"].default

        return value


class Jwk(BaseModel):
    """The JSON Web Key signature parameters of the ManifestV1 model.
    These parameters should describe the DSS (Elliptic Curve) used to sign the manifest.

    See:
        Read the RFC7517 to learn more: https://datatracker.ietf.org/doc/html/rfc7517.

    Attributes:
        crv (Optional): The prime modulus of the curve.
        kid: (Optional): The key ID used to match a specific key.
        kty (Optional): The key type that identify the used cryptographic algorithm
            family.
        x (Optional): The x base64url-encoded coordinate value used to compute the curve.
        y (Optional): The y base64url-encoded coordinate value used to compute the curve.
    """

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
    """The header that contains the signature parameters of the ManifestV1 model.

    See:
        Read the RFC7517 to learn more: https://datatracker.ietf.org/doc/html/rfc7517.

    Attributes:
        jwk (Optional): The JSON Web Key signature parameters.
        alg (Optional): The algorithm intended for use with the key.
    """

    jwk: Optional[Jwk] = None
    alg: Optional[str] = ""

    @validator("*")
    def force_default(cls, value: Any, values: dict[str, Any], **kwargs: Any) -> Any:
        if value is None:
            return kwargs["field"].default

        return value


class Signature(BaseModel):
    """The signature of the image manifest for the ManifestV1 model.

    Attributes:
        header (Optional): The signature parameters.
        signature (Optional): The signature of the image manifest.
        protected (Optional): The signed protected header.
    """

    header: Optional[Header] = None
    signature: Optional[str] = ""
    protected: Optional[str] = ""

    @validator("*")
    def force_default(cls, value: Any, values: dict[str, Any], **kwargs: Any) -> Any:
        if value is None:
            return kwargs["field"].default

        return value


class ManifestV1(BaseModel):
    """The manifest (version 1) model definition.

    Attributes:
        schema_version (Optional): The schema version of the manifest.
            Should be always 1.
        name (Optional): The name of the image's repository.
        tag (Optional): The tag of the image.
        architecture (Optional): The host architecture on which the image should run.
        fs_layers (Optional): The list of layers that compose the image defined
            by the manifest.
        history (Optional): The list of unstructured historical data that describe the
            statements that define the image.
        signatures (Optional): The list of the signatures of the manifest.
    """

    def __init__(self, **data: Any) -> None:
        """The custom model constructor.
        Raise a warning message if the ManifestV1 model is used.

        Args:
            **data: The model data.
        """

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
