from typing import Any, Optional
from pydantic import BaseModel, Field, validator

__all__: list[str] = [
    "Tags",
]


class Tags(BaseModel):
    """The reposiroty tags model definition.

    Attributes:
        name (Optional): The repository name.
        tags (Optional): The tags list of the repository.
    """

    name: Optional[str] = ""
    tags: Optional[list[str]] = Field([])

    @validator("*")
    def force_default(cls, value: Any, values: dict[str, Any], **kwargs: Any) -> Any:
        if value is None:
            return kwargs["field"].default

        return value
