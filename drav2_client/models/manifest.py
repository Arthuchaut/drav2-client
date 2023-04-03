from typing import Optional
from pydantic import BaseModel, Field
from drav2_client.types import ManifestMediaType

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
    media_type: Optional[str] = Field("", alias="mediaType")
    size: Optional[int] = None
    digest: Optional[str] = ""


class Layer(BaseModel):
    media_type: Optional[str] = Field("", alias="mediaType")
    size: Optional[int] = None
    digest: Optional[str] = ""


class ManifestV2(BaseModel):
    schema_version: Optional[int] = Field(None, alias="schemaVersion")
    media_type: Optional[ManifestMediaType] = Field(None, alias="mediaType")
    config: Optional[Config] = None
    layers: Optional[list[Layer]] = Field([])


class FsLayer(BaseModel):
    blob_sum: Optional[str] = Field("", alias="blobSum")


class HistoryItem(BaseModel):
    v1_compatibility: Optional[str] = Field("", alias="v1Compatibility")


class Jwk(BaseModel):
    crv: Optional[str] = ""
    kid: Optional[str] = ""
    kty: Optional[str] = ""
    x: Optional[str] = ""
    y: Optional[str] = ""


class Header(BaseModel):
    jwk: Optional[Jwk] = None
    alg: Optional[str] = ""


class Signature(BaseModel):
    header: Optional[Header] = None
    signature: Optional[str] = ""
    protected: Optional[str] = ""


class ManifestV1(BaseModel):
    schema_version: Optional[int] = Field(None, alias="schemaVersion")
    name: Optional[str] = ""
    tag: Optional[str] = ""
    architecture: Optional[str] = ""
    fs_layers: Optional[list[FsLayer]] = Field(None, alias="fsLayers")
    history: Optional[list[HistoryItem]] = Field([])
    signatures: Optional[list[Signature]] = Field([])
