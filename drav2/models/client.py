from base64 import b64encode
from functools import cached_property
from typing import Any, ClassVar
from pydantic import BaseModel, validator

__all__: list[str] = [
    "Logins",
]


class Logins(BaseModel):
    """The credentials model for the registry authentication.

    Attributes:
        user_id: The user identifier.
        password: The password.
    """

    user_id: str
    password: str

    @cached_property
    def b64_encoded(self) -> str:
        """Build the base64 encoded string from the credentials.

        Returns:
            str: The base64url-encoded credentials.
        """

        # fmt: off
        return b64encode(f"{self.user_id}:{self.password}".encode("utf8")).decode("utf8")
        # fmt: on

    @validator("*")
    def ensure_value_not_empty(
        cls, value: str, values: dict[str, Any], **kwargs: Any
    ) -> str:
        if not value:
            raise TypeError("The str value cannot be empty.")
        return value

    class Config:
        # Must be defined to prevent TypeError exception when using cached_property
        keep_untouched: ClassVar[tuple[type[Any]]] = (cached_property,)
