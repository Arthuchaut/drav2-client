from functools import cached_property
from typing import Any, ClassVar, Iterator, Literal, Optional
import httpx
from pydantic import BaseModel

__all__: list[str] = [
    "Blob",
    "UnreadableError",
]


class Blob(BaseModel):
    """The layer's blob model definition.

    Attributes:
        content (Property): The binary data of the blob.
            This property must be only use in a non-stream mode context.
    """

    _res: httpx.Response

    def __init__(self, *, res: Optional[httpx.Response] = None, **data: Any) -> None:
        """The custom constructor.

        Args:
            res (Optional): The HTTP response object.
        """

        super().__init__(**data)
        self._res = res

    @cached_property
    def content(self) -> bytes:
        """The blob binary data.
        Should be called in a non-stream mode context.

        Raises:
            UnreadableError: If the property is called in a streaming context.

        Returns:
            bytes: The blob's binary data.
        """

        try:
            return self._res.content
        except httpx.ResponseNotRead:
            raise UnreadableError(
                "Cannot read the blob content directly. "
                "Make sure you are not in streaming mode."
            )

    def iter_bytes(self, chunk_size: int = 1024) -> Iterator[bytes]:
        """Retrieve each chunk of the blob's binary data from the remote server.

        Args:
            chunk_size (Optional): The maximum size (in Bytes) of the retrieved chunks.
                Default to 1024.

        Returns:
            Iterator[bytes]: A generator of bytes.
        """

        try:
            yield from self._res.iter_bytes(chunk_size=chunk_size)
        finally:
            self._res.close()

    class Config:
        # Must be defined to prevent TypeError exception when using cached_property
        keep_untouched: ClassVar[tuple[type[Any]]] = (cached_property,)
        underscore_attrs_are_private: ClassVar[Literal[True]] = True


class UnreadableError(Exception):
    ...
