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


class Manifest(BaseModel):
    schema_version: Optional[int] = Field(None, alias="schemaVersion")
    name: Optional[str] = ""
    tag: Optional[str] = ""
    architecture: Optional[str] = ""
    fs_layers: Optional[list[FsLayer]] = Field([], alias="fsLayers")
    history: Optional[list[HistoryItem]] = Field([])
    signatures: Optional[list[Signature]] = Field([])
