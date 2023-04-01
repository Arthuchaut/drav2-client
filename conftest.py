import json
import re
from typing import Any, Callable, Final, Optional
from urllib.parse import urljoin
import httpx
import pytest
from drav2_client.client import RegistryClient

_FAKE_BASE_URL: Final[str] = "http://fake_host/v2/"


class MockedResponse:
    def __init__(self, status_code: int, text: str) -> None:
        self.status_code: int = status_code
        self.text: str = text

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
        route: str, expected_obj: dict[str, Any], *, status_code: Optional[int] = 200
    ) -> Callable[[str, Any], MockedResponse]:
        def get(self, url: str, **kwargs: Any) -> MockedResponse:
            if re.search(urljoin(_FAKE_BASE_URL, route), url):
                return MockedResponse(
                    status_code=status_code, text=json.dumps(expected_obj)
                )

        return get

    return wrapper
