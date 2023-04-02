from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, validator

__all__: list[str] = [
    "RegistryResponse",
    "Headers",
]


class Headers(BaseModel):
    content_type: Optional[str] = Field("", alias="content-type")
    docker_distribution_api_version: Optional[str] = Field(
        "",
        alias="docker-distribution-api-version",
    )
    x_content_type_options: Optional[str] = Field(
        "",
        alias="x-content-type-options",
    )
    docker_content_digest: Optional[str] = Field("", alias="docker-content-digest")
    etag: Optional[str] = Field("", alias="etag")
    date: Optional[datetime] = None
    content_length: Optional[int] = Field(0, alias="content-length")

    @validator("date", pre=True)
    def parse_date(cls, value: str | None) -> datetime | None:
        if value:
            # Sat, 01 Apr 2023 23:18:26 GMT
            return datetime.strptime(value, "%a, %d %b %Y %H:%M:%S %Z")


class RegistryResponse(BaseModel):
    status_code: int
    headers: Headers
    result: BaseModel
