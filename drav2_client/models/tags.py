from typing import Optional
from pydantic import BaseModel, Field

__all__: list[str] = [
    "Tags",
]


class Tags(BaseModel):
    name: Optional[str] = ""
    tags: Optional[list[str]] = Field([])
