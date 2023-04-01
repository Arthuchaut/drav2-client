from typing import Optional
from pydantic import BaseModel, Field

__all__: list[str] = [
    "TagsList",
]


class TagsList(BaseModel):
    name: Optional[str] = None
    tags: Optional[list[str]] = Field([])
