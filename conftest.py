import json
import re
from typing import Any, Callable, Final, Optional
from urllib.parse import urljoin
import httpx
import pytest
from drav2_client.client import RegistryClient

_FAKE_BASE_URL: Final[str] = "http://fake_host/v2/"


class MockedResponse:
    def __init__(self, status_code: int, headers: dict[str, str], text: str) -> None:
        self.status_code: int = status_code
        self.headers: dict[str, str] = headers
        self.text: str = text
        self.content: bytes = text.encode("utf8")

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("Error", request=None, response=None)

    def json(self) -> dict[str, Any]:
        return json.loads(self.text)


@pytest.fixture
def client() -> RegistryClient:
    return RegistryClient(_FAKE_BASE_URL)


@pytest.fixture
def get_patch() -> Callable[[Any], Any]:
    def wrapper(
        route: str,
        *,
        dict_obj: Optional[dict[str, Any]] = {},
        bytes_obj: Optional[bytes] = b"",
        headers: Optional[dict[str, str]] = {},
        status_code: Optional[int] = 200
    ) -> Callable[[str, Any], MockedResponse]:
        def get(self, url: str, **kwargs: Any) -> MockedResponse | None:
            if re.search(urljoin(_FAKE_BASE_URL, route), url):
                text: str = bytes_obj.decode("utf8")

                if dict_obj:
                    text = json.dumps(dict_obj)

                return MockedResponse(
                    status_code=status_code, headers=headers, text=text
                )

        return get

    return wrapper
