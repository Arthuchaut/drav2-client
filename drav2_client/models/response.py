from datetime import datetime
import enum
import re
from typing import Any, Final, Optional
from pydantic import BaseModel, Field, validator
from urllib.parse import urlparse, parse_qs

__all__: list[str] = [
    "RegistryResponse",
    "Headers",
    "Errors",
    "Error",
    "Detail",
]

_LINK_URI_PATTERN: Final[re.Pattern] = re.compile(r"<(?P<uri>.+)>")


class Link(BaseModel):
    size: int
    last: str


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
    www_authenticate: Optional[str] = Field("", alias="www-authenticate")
    docker_content_digest: Optional[str] = Field("", alias="docker-content-digest")
    docker_upload_uuid: Optional[str] = Field("", alias="docker-upload-uuid")
    etag: Optional[str] = ""
    date: Optional[datetime] = None
    range: Optional[int] = None
    location: Optional[str] = ""
    content_length: Optional[int] = Field(0, alias="content-length")
    content_range: Optional[int] = Field(None, alias="content-range")
    link: Optional[Link] = None

    @validator("date", pre=True)
    def parse_date(cls, value: str | None) -> datetime | None:
        if value:
            # Sat, 01 Apr 2023 23:18:26 GMT
            return datetime.strptime(value, "%a, %d %b %Y %H:%M:%S %Z")

    @validator("link", pre=True)
    def parse_link(cls, value: str | None) -> Link | None:
        if value and (match := _LINK_URI_PATTERN.search(value)):
            # <<uri>?n=<n from the request>&last=<last repository in response>>; rel="next"
            qs: dict[str, list[str]] = parse_qs(urlparse(match.group("uri")).query)
            return Link(last=qs["last"][0], size=qs["n"][0])

    @validator("*")
    def force_default(cls, value: Any, values: dict[str, Any], **kwargs: Any) -> Any:
        if value is None:
            return kwargs["field"].default

        return value


class Detail(BaseModel):
    name: Optional[str] = ""
    tag: Optional[str] = Field("", alias="Tag")
    digest: Optional[str] = ""

    @validator("*")
    def force_default(cls, value: Any, values: dict[str, Any], **kwargs: Any) -> Any:
        if value is None:
            return kwargs["field"].default

        return value


class Error(BaseModel):
    class Code(str, enum.Enum):
        BLOB_UNKNOWN = "BLOB_UNKNOWN"
        BLOB_UPLOAD_INVALID = "BLOB_UPLOAD_INVALID"
        BLOB_UPLOAD_UNKNOWN = "BLOB_UPLOAD_UNKNOWN"
        DIGEST_INVALID = "DIGEST_INVALID"
        MANIFEST_BLOB_UNKNOWN = "MANIFEST_BLOB_UNKNOWN"
        MANIFEST_INVALID = "MANIFEST_INVALID"
        MANIFEST_UNKNOWN = "MANIFEST_UNKNOWN"
        MANIFEST_UNVERIFIED = "MANIFEST_UNVERIFIED"
        NAME_INVALID = "NAME_INVALID"
        NAME_UNKNOWN = "NAME_UNKNOWN"
        PAGINATION_NUMBER_INVALID = "PAGINATION_NUMBER_INVALID"
        RANGE_INVALID = "RANGE_INVALID"
        SIZE_INVALID = "SIZE_INVALID"
        TAG_INVALID = "TAG_INVALID"
        UNAUTHORIZED = "UNAUTHORIZED"
        DENIED = "DENIED"
        UNSUPPORTED = "UNSUPPORTED"
        INTERNAL_ERROR = "INTERNAL_ERROR"

    code: Optional[Code] = None
    message: Optional[str] = ""
    detail: Optional[Detail] = None

    @validator("*")
    def force_default(cls, value: Any, values: dict[str, Any], **kwargs: Any) -> Any:
        if value is None:
            return kwargs["field"].default

        return value


class Errors(BaseModel):
    errors: Optional[list[Error]] = Field([])

    @validator("*")
    def force_default(cls, value: Any, values: dict[str, Any], **kwargs: Any) -> Any:
        if value is None:
            return kwargs["field"].default

        return value


class RegistryResponse(BaseModel):
    class Status(enum.IntEnum):
        OK = 200
        CREATED = 201
        ACCEPTED = 202
        NON_AUTHORITATIVE_INFORMATION = 203
        NO_CONTENT = 204
        RESET_CONTENT = 205
        PARTIAL_CONTENT = 206
        FOUND = 302
        TEMPORARY_REDIRECT = 307
        BAD_REQUEST = 400
        UNAUTHORIZED = 401
        FORBIDDEN = 403
        NOT_FOUND = 404
        TOO_MANY_REQUESTS = 429
        METHOD_NOT_ALLOWED = 405
        INTERNAL_SERVER_ERROR = 500
        NOT_IMPLEMENTED = 501
        BAD_GATEWAY = 502
        SERVICE_UNAVAILABLE = 503
        GATEWAY_TIMEOUT = 504
        HTTP_VERSION_NOT_SUPPORTED = 505
        VARIANT_ALSO_NEGOTIATES = 506
        INSUFFICIENT_STORAGE = 507
        LOOP_DETECTED = 508
        NOT_EXTENDED = 510
        NETWORK_AUTHENTICATION_REQUIRED = 511

    status_code: Status
    headers: Headers
    body: Optional[BaseModel] = None

    @validator("*")
    def force_default(cls, value: Any, values: dict[str, Any], **kwargs: Any) -> Any:
        if value is None:
            return kwargs["field"].default

        return value
