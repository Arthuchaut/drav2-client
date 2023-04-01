from typing import Optional
from pydantic import BaseModel, Field

__all__: list[str] = [
    "Manifest",
    "Signature",
    "Header",
    "Jwk",
    "HistoryItem",
    "FsLayer",
]


class FsLayer(BaseModel):
    blob_sum: Optional[str] = Field(None, alias="blobSum")


class HistoryItem(BaseModel):
    v1_compatibility: Optional[str] = Field(None, alias="v1Compatibility")


class Jwk(BaseModel):
    crv: Optional[str] = None
    kid: Optional[str] = None
    kty: Optional[str] = None
    x: Optional[str] = None
    y: Optional[str] = None


class Header(BaseModel):
    jwk: Optional[Jwk] = None
    alg: Optional[str] = None


class Signature(BaseModel):
    header: Optional[Header] = None
    signature: Optional[str] = None
    protected: Optional[str] = None


class Manifest(BaseModel):
    schema_version: Optional[int] = Field(None, alias="schemaVersion")
    name: Optional[str] = None
    tag: Optional[str] = None
    architecture: Optional[str] = None
    fs_layers: Optional[list[FsLayer]] = Field([], alias="fsLayers")
    history: Optional[list[HistoryItem]] = Field([])
    signatures: Optional[list[Signature]] = Field([])
