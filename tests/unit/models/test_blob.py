from typing import Any, Callable
from pydantic import ValidationError
import pytest
from drav2_client.models.blob import Blob
from conftest import fake_iter_bytes


class TestBlob:
    @pytest.mark.parametrize(
        "data, expected, throwable",
        [
            (
                {
                    "content": b"hello world!",
                },
                Blob.construct(
                    content=b"hello world!",
                    iter_bytes=Blob._undefined_iter_bytes,
                ),
                None,
            ),
            (
                {},
                Blob.construct(iter_bytes=Blob._undefined_iter_bytes),
                None,
            ),
            (
                {
                    "iter_bytes": fake_iter_bytes,
                },
                Blob.construct(iter_bytes=fake_iter_bytes),
                None,
            ),
            (
                {
                    "content": [],
                    "iter_bytes": "world",
                },
                (".content",),
                ValidationError,
            ),
        ],
    )
    def test_init(
        self,
        data: dict[str, Any],
        expected: Blob | tuple[str, ...],
        throwable: type[ValidationError] | None,
        extract_error_list: Callable[[Any], Any],
        assert_sequences_equals: Callable[[Any], Any],
    ) -> None:
        if throwable:
            try:
                Blob.parse_obj(data)
                raise AssertionError(f"Did not raise {throwable}")  # pragma: no cover
            except throwable as e:
                error_list: list[str] = extract_error_list(e)
                assert_sequences_equals(error_list, expected)
        else:
            assert Blob.parse_obj(data) == expected

    def test_blob_with_undefined_iter_bytes(self) -> None:
        blob: Blob = Blob(content=b"hello")

        with pytest.raises(NotImplementedError):
            blob.iter_bytes()
