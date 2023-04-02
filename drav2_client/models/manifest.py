from typing import Optional
from pydantic import BaseModel, Field

__all__: list[str] = [
    "Manifest",
    "Layer",
    "Config",
]


class Config(BaseModel):
    media_type: Optional[str] = Field("", alias="mediaType")
    size: Optional[int] = None
    digest: Optional[str] = ""


class Layer(BaseModel):
    media_type: Optional[str] = Field("", alias="mediaType")
    size: Optional[int] = None
    digest: Optional[str] = ""


class Manifest(BaseModel):
    schema_version: Optional[int] = Field(None, alias="schemaVersion")
    media_type: Optional[str] = Field("", alias="mediaType")
    config: Optional[Config] = None
    layers: Optional[list[Layer]] = Field([])
