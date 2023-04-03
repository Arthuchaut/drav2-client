from typing import Any, ClassVar, Optional
from pydantic import BaseModel, Field, validator

__all__: list[str] = [
    "Tags",
]


class Tags(BaseModel):
    name: Optional[str] = ""
    tags: Optional[list[str]] = Field([])

    @validator("*")
    def force_default(cls, value: Any, values: dict[str, Any], **kwargs: Any) -> Any:
        if value is None:
            return kwargs["field"].default

        return value
