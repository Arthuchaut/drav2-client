import enum
from typing import Any, Optional
from pydantic import BaseModel, Field, validator

from drav2_client.types import SHA256


__all__: list[str] = [
    "Errors",
    "Error",
]


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
    detail: Any = None

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
