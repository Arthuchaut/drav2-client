from __future__ import annotations
from datetime import datetime
import enum
import re
from typing import Any, ClassVar, Final, Generic, Literal, Optional, TYPE_CHECKING
import httpx
from pydantic import BaseModel, Field, validator
from urllib.parse import ParseResult, urlparse, parse_qs
from drav2_client.models.manifest import ManifestV1, ManifestV2
from drav2_client.types import SHA256, T

# To prevent circular import on runtime
if TYPE_CHECKING:
    from drav2_client.client import RegistryClient

__all__: list[str] = [
    "RegistryResponse",
    "Headers",
    "Link",
    "Range",
    "Location",
]

_LINK_URI_PATTERN: Final[re.Pattern] = re.compile(r"<(?P<uri>.+)>")
_RANGE_PATTERN: Final[re.Pattern] = re.compile(
    r"(?P<type>bytes=)?(?P<start>\d+)-(?P<offset>\d+)"
)


class Link(BaseModel):
    """The header's link model definition.

    Attributes:
        size: The maximum length of the resource's results.
        last: The last element of the resource from which the pagination should be
            begining.
    """

    size: int
    last: str


class Range(BaseModel):
    """The bytes interval definition.

    Attributes:
        type (Optional): The type of the bytes range. Must be always "bytes".
        start: The start part of the bytes range.
        offset: The interval bytes offset.
    """

    type: Literal["bytes"] = "bytes"
    start: int
    offset: int


class Location(BaseModel):
    """The header's location model definition.

    Attributes:
        url: The whole URL string.
        scheme (Optional): The protocol part of the URL (should be "http" or "https").
        netloc (Optional): The <hostname>[:<port>] part of the URL.
        path (Optional): The path part of the URL.
        params (Optional): The params part of the URL. Notice that the params is
            different of the query. See the RFC3986 to learn more:
            https://datatracker.ietf.org/doc/html/rfc3986#section-3.3.
        query (Optional): The query part of the URL.
        fragment (Optional): The fragment part of the URL.
            See the RFC3986 to learn more:
            https://datatracker.ietf.org/doc/html/rfc3986#section-3.5.
    """

    url: str
    scheme: Optional[str] = ""
    netloc: Optional[str] = ""
    path: Optional[str] = ""
    params: Optional[dict[str, str]] = Field({})
    query: Optional[dict[str, str]] = Field({})
    fragment: Optional[str] = ""
    _client: Optional["RegistryClient"] = None

    def __init__(self, **data: Any) -> None:
        """The custom model constructor.
        Parse and fill the URL parts.

        Args:
            **data: The model metadata.
        """

        super().__init__(**data)
        parsed_url: ParseResult = urlparse(self.url)
        self.scheme = parsed_url.scheme
        self.netloc = parsed_url.netloc
        self.path = parsed_url.path
        self.params = {
            key: val[0]
            for key, val in parse_qs(
                parsed_url.params, encoding="utf8", separator=";"
            ).items()
        }
        self.query = {
            key: val[0]
            for key, val in parse_qs(parsed_url.query, encoding="utf8").items()
        }
        self.fragment = parsed_url.fragment

    def go(self) -> RegistryResponse:
        """Request the location URL.

        Returns:
            RegistryResponse: The response from the remote registry.
        """

        res: httpx.Response = self._client._client.get(
            f"{self.scheme}://{self.netloc}{self.path}",
            headers=self._client._auth_header,
            params=self.query,
        )
        return self._client._build_response(res)

    class Config:
        underscore_attrs_are_private: ClassVar[Literal[True]] = True


class Headers(BaseModel):
    """The HTTP response headers from the registry.

    Attributes:
        content_type (Optional): The media type of the body.
        docker_distribution_api_version (Optional): The registry API version.
        x_content_type_options (Optional): The marker of the MIME type.
        www_authenticate (Optional): The authentication method that should be used if
            any authentication error is raised by the server.
        docker_content_digest (Optional): The hash of the targeted content of the request.
        docker_upload_uuid (Optional): The blob upload uuid.
        etag (Optional): Identify the version of the given resource.
        date (Optional): The origin datetime of the request.
        range (Optional): The bytes interval of the given resource.
        location (Optional): The resource location information.
        content_length (Optional): The resource content size.
        content_range (Optional): The bytes interval of the uploaded blob.
        accept_ranges (Optional): The expected type of the range. Should be always bytes.
        link (Optional): The resource location in pagination mode.
    """

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
    docker_content_digest: Optional[SHA256] = Field(None, alias="docker-content-digest")
    docker_upload_uuid: Optional[str] = Field("", alias="docker-upload-uuid")
    etag: Optional[str] = ""
    date: Optional[datetime] = None
    range: Optional[Range] = None
    location: Optional[Location] = None
    content_length: Optional[int] = Field(None, alias="content-length")
    content_range: Optional[Range] = Field(None, alias="content-range")
    accept_ranges: Optional[str] = Field("", alias="accept-ranges")
    link: Optional[Link] = None

    @validator("date", pre=True)
    def parse_date(cls, value: str | None) -> datetime | None:
        if value:
            # Sat, 01 Apr 2023 23:18:26 GMT
            return datetime.strptime(value, "%a, %d %b %Y %H:%M:%S %Z")

    @validator("location", pre=True)
    def parse_location(cls, value: str | None) -> Location | None:
        if value:
            return Location(url=value)

    @validator("range", "content_range", pre=True)
    def parse_range(cls, value: str | None) -> Range | None:
        if value and (match := _RANGE_PATTERN.search(value)):
            type_: str = match.group("type") or "bytes"
            return Range(
                type=type_, start=match.group("start"), offset=match.group("offset")
            )

    @validator("link", pre=True)
    def parse_link(cls, value: str | None) -> Link | None:
        if value and (match := _LINK_URI_PATTERN.search(value)):
            # <<uri>?n=<n from the request>&last=<last repository in response>>; rel="next"
            qs: dict[str, list[str]] = parse_qs(urlparse(match.group("uri")).query)
            return Link(last=qs["last"][0], size=qs["n"][0])

    @validator("docker_content_digest", pre=True)
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


class RegistryResponse(BaseModel, Generic[T]):
    """The registry response model definition.
    Should be used to parse and return any response from the remote registry.

    Attributes:
        status_code: The response HTTP status code.
        headers: The response headers.
        body (Optional): The response body is any.
    """

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

    status_code: RegistryResponse.Status
    headers: Headers
    body: Optional[T] = None

    def __init__(self, *, additional_meta: dict[str, Any] = {}, **data: Any) -> None:
        """The custom model constructor.

        Args:
            additional_meta (Optional): Any additional metadata which will be given to
                the concerned models to enrich them.
            **data: The model metadata (the body of the registry response).
        """

        super().__init__(**data)

        if self.headers.location is not None:
            self.headers.location._client = additional_meta.get("client")
        if isinstance(self.body, ManifestV2):
            for layer in self.body.layers:
                layer._client = additional_meta.get("client")
                layer._name = additional_meta.get("name")
        if isinstance(self.body, ManifestV1):
            for layer in self.body.fs_layers:
                layer._client = additional_meta.get("client")
                layer._name = self.body.name

    @validator("*")
    def force_default(cls, value: Any, values: dict[str, Any], **kwargs: Any) -> Any:
        if value is None:
            return kwargs["field"].default

        return value
