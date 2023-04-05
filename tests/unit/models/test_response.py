import datetime
from typing import Any, Callable
from pydantic import ValidationError
import pytest
from drav2_client.models.catalog import Catalog
from drav2_client.models.response import Headers, Link, RegistryResponse


class TestResponse:
    @pytest.mark.parametrize(
        "data, expected, throwable",
        [
            (
                {
                    "status_code": 200,
                    "headers": {
                        "content-type": "application/json",
                        "docker-content-digest": "sha256:54e726b437fb92dd7b43f4dd5cd79b01a1e96a22849b2fc2ffeb34fac2d65440",
                        "link": '</path/to/resource/?last=python&n=10> rel="link"',
                        "date": "Sat, 01 Apr 2023 23:18:26 GMT",
                    },
                    "body": Catalog.construct(repositories=["python", "debian"]),
                },
                RegistryResponse.construct(
                    status_code=RegistryResponse.Status.OK,
                    headers=Headers.construct(
                        content_type="application/json",
                        docker_content_digest="sha256:54e726b437fb92dd7b43f4dd5cd79b01a1e96a22849b2fc2ffeb34fac2d65440",
                        link=Link(last="python", size=10),
                        date=datetime.datetime(2023, 4, 1, 23, 18, 26),
                    ),
                    body=Catalog.construct(repositories=["python", "debian"]),
                ),
                None,
            ),
            (
                {
                    "status_code": 200,
                    "headers": {},
                },
                RegistryResponse.construct(
                    status_code=RegistryResponse.Status.OK,
                    headers=Headers.construct(),
                    body=None,
                ),
                None,
            ),
            (
                {
                    "status_code": 200,
                    "headers": {
                        "content-type": None,
                    },
                    "body": None,
                },
                RegistryResponse.construct(
                    status_code=RegistryResponse.Status.OK,
                    headers=Headers.construct(
                        content_type="",
                    ),
                    body=None,
                ),
                None,
            ),
            (
                {
                    "status_code": 200,
                    "headers": {},
                    "body": b"blob",
                },
                RegistryResponse.construct(
                    status_code=RegistryResponse.Status.OK,
                    headers=Headers.construct(),
                    body=b"blob",
                ),
                None,
            ),
            (
                {
                    "status_code": 600,
                    "headers": "hello",
                    "body": object(),
                },
                (
                    ".status_code",
                    ".headers",
                    ".body",
                ),
                ValidationError,
            ),
            (
                {
                    "status_code": 600,
                    "headers": {
                        "docker-content-digest": "sha256:szuzs64d8hd54",
                    },
                    "body": object(),
                },
                (
                    ".status_code",
                    ".headers.docker-content-digest",
                    ".body",
                ),
                ValidationError,
            ),
        ],
    )
    def test_init(
        self,
        data: dict[str, Any],
        expected: RegistryResponse | tuple[str, ...],
        throwable: type[ValidationError] | None,
        extract_error_list: Callable[[Any], Any],
        assert_sequences_equals: Callable[[Any], Any],
    ) -> None:
        if throwable:
            try:
                RegistryResponse(**data)
                raise AssertionError(f"Did not raise {throwable}")  # pragma: no cover
            except throwable as e:
                error_list: list[str] = extract_error_list(e)
                assert_sequences_equals(error_list, expected)
        else:
            assert RegistryResponse(**data) == expected
