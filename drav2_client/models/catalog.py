from typing import Optional
from pydantic import BaseModel, Field

__all__: list[str] = [
    "Catalog",
]


class Catalog(BaseModel):
    repositories: Optional[list[str]] = Field([])
