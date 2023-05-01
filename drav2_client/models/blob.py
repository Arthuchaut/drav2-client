from typing import Any, Callable, Iterator, Optional
from pydantic import BaseModel, validator

__all__: list[str] = [
    "Blob",
]


class Blob(BaseModel):
    content: Optional[bytes] = None
    iter_bytes: Optional[Callable[[int], Iterator[bytes]]] = None

    @validator("iter_bytes", pre=True, always=True)
    def ensure_callable(
        cls, value: Callable[[int], Iterator[bytes]] | None
    ) -> Callable[[Any], Any]:
        if callable(value):
            return value

        return cls._undefined_iter_bytes

    @classmethod
    def _undefined_iter_bytes(cls, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError(
            f"Cannot iterate through the bytes content since the 'stream' argument "
            f"is 'False'. Please, ensure that the 'stream' option is enabled in "
            f"the get_<resource>() method or use the '{cls.__class__}.content' "
            f"field to read the whole bytes content."
        )
