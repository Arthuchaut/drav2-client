import json
import re
from typing import Any, Callable, Final, Iterable, Iterator, Optional
from urllib.parse import urljoin
import httpx
from pydantic import ValidationError
import pytest
from drav2_client.client import RegistryClient

_FAKE_BASE_URL: Final[str] = "http://fake_host/v2/"


class MockedResponse:
    def __init__(self, status_code: int, headers: dict[str, str], text: str) -> None:
        self.status_code: int = status_code
        self.headers: dict[str, str] = headers
        self.text: str = text
        self.content: bytes = text.encode("utf8")

    def json(self) -> dict[str, Any]:
        return json.loads(self.text)

    def iter_bytes(self, chunk_size: int | None = None) -> Iterator[bytes]:
        if chunk_size is None or len(self.content) >= chunk_size:
            yield self.content
        else:
            for chunk_loc in range(0, len(self.content), chunk_size):
                yield self.content[chunk_loc : chunk_loc + chunk_size]

    def close(self) -> None:
        pass


@pytest.fixture
def client() -> RegistryClient:
    return RegistryClient(_FAKE_BASE_URL)


@pytest.fixture
def request_patch() -> Callable[[Any], Any]:
    def wrapper(
        route: str,
        *,
        dict_obj: Optional[dict[str, Any]] = {},
        bytes_obj: Optional[bytes] = b"",
        headers: Optional[dict[str, str]] = {},
        status_code: Optional[int] = 200,
    ) -> Callable[[str, Any], MockedResponse]:
        def method(self, url: str, **kwargs: Any) -> MockedResponse | None:
            if re.search(urljoin(_FAKE_BASE_URL, route), url):
                text: str = bytes_obj.decode("utf8")

                if dict_obj:
                    text = json.dumps(dict_obj)

                return MockedResponse(
                    status_code=status_code, headers=headers, text=text
                )

        return method

    return wrapper


@pytest.fixture
def send_patch() -> Callable[[Any], Any]:
    def wrapper(
        route: str,
        *,
        dict_obj: Optional[dict[str, Any]] = {},
        bytes_obj: Optional[bytes] = b"",
        headers: Optional[dict[str, str]] = {},
        status_code: Optional[int] = 200,
    ) -> Callable[[str, Any], MockedResponse]:
        def send(self, req: httpx.Request, **kwargs: Any) -> MockedResponse | None:
            if re.search(urljoin(_FAKE_BASE_URL, route), str(req.url)):
                text: str = bytes_obj.decode("utf8")

                if dict_obj:
                    text = json.dumps(dict_obj)

                return MockedResponse(
                    status_code=status_code, headers=headers, text=text
                )

        return send

    return wrapper


@pytest.fixture
def extract_error_list() -> Callable[[Any], Any]:
    def wrapper(error: ValidationError) -> list[str]:
        fpaths: list[str] = []

        for error in error.errors():
            fpath: str = ""

            for slice_ in error["loc"]:
                if type(slice_) is int:
                    fpath += f"[{slice_}]"
                else:
                    fpath += "." + slice_

            fpaths.append(fpath)

        return fpaths

    return wrapper


@pytest.fixture
def assert_sequences_equals() -> Callable[[Any], Any]:
    def wrapper(
        model_errors_list: Iterable[str], expected_errors_list: Iterable[str]
    ) -> None:
        model_unmatched: list[str] = []
        expected_unmatched: list[str] = []

        for fpath1 in list(model_errors_list):
            for fpath2 in list(expected_errors_list):
                if fpath1 == fpath2:
                    break
            else:
                model_unmatched.append(fpath1)  # pragma: no cover

        for fpath1 in list(expected_errors_list):
            for fpath2 in list(model_errors_list):
                if fpath1 == fpath2:
                    break
            else:
                expected_unmatched.append(fpath1)  # pragma: no cover

        if model_unmatched or expected_unmatched:
            raise AssertionError(
                f"Unexpected validation errors from "
                f"model_unmatched={model_unmatched}, "
                f"expected_unmatched={expected_unmatched}"
            ) from None  # pragma: no cover

    return wrapper


def fake_iter_bytes(*args: Any, **kwargs: Any) -> None:  # pragma: no cover
    pass
