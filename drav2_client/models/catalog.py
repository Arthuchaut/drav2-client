from typing import Any, Optional
from pydantic import BaseModel, Field, validator

__all__: list[str] = [
    "Catalog",
]


class Catalog(BaseModel):
    repositories: Optional[list[str]] = Field([])

    @validator("*")
    def force_default(cls, value: Any, values: dict[str, Any], **kwargs: Any) -> Any:
        if value is None:
            return kwargs["field"].default

        return value
