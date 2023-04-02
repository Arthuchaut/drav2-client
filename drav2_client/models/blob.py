from pydantic import BaseModel

__all__: list[str] = [
    "Blob",
]


class Blob(BaseModel):
    content: bytes
