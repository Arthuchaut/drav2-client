from functools import cached_property
from typing import Any, ClassVar, Iterator, Optional
import httpx
from pydantic import BaseModel

__all__: list[str] = [
    "Blob",
    "UnreadableError",
]


class Blob(BaseModel):
    _res: httpx.Response

    def __init__(self, *, res: Optional[httpx.Response] = None, **data: Any) -> None:
        super().__init__(**data)
        self._res = res

    @cached_property
    def content(self) -> bytes:
        try:
            return self._res.content
        except httpx.ResponseNotRead:
            raise UnreadableError(
                "Cannot read the blob content directly. "
                "Make sure you are not in streaming mode."
            )

    def iter_bytes(self, chunk_size: int = 1024) -> Iterator[bytes]:
        try:
            yield from self._res.iter_bytes(chunk_size=chunk_size)
        finally:
            self._res.close()

    class Config:
        # Must be defined to prevent TypeError exception when using cached_property
        keep_untouched: ClassVar[tuple[type[Any]]] = (cached_property,)
        underscore_attrs_are_private: bool = True


class UnreadableError(Exception):
    ...
