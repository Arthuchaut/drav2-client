from typing import Any, Callable
from pydantic import ValidationError
import pytest
from drav2_client.models.tags import Tags


class TestTags:
    @pytest.mark.parametrize(
        "data, expected, throwable",
        [
            (
                {
                    "name": "python",
                    "tags": [
                        "latest",
                        "slim-bullseye",
                    ],
                },
                Tags.construct(
                    name="python",
                    tags=[
                        "latest",
                        "slim-bullseye",
                    ],
                ),
                None,
            ),
            (
                {},
                Tags.construct(
                    name="",
                    tags=[],
                ),
                None,
            ),
            (
                {
                    "name": None,
                    "tags": None,
                },
                Tags.construct(
                    name="",
                    tags=[],
                ),
                None,
            ),
            (
                {
                    "name": [],
                    "tags": "hello",
                },
                (".name", ".tags"),
                ValidationError,
            ),
        ],
    )
    def test_init(
        self,
        data: dict[str, Any],
        expected: Tags | tuple[str, ...],
        throwable: type[ValidationError] | None,
        extract_error_list: Callable[[Any], Any],
        assert_sequences_equals: Callable[[Any], Any],
    ) -> None:
        if throwable:
            try:
                Tags.parse_obj(data)
                raise AssertionError(f"Did not raise {throwable}")  # pragma: no cover
            except throwable as e:
                error_list: list[str] = extract_error_list(e)
                assert_sequences_equals(error_list, expected)
        else:
            assert Tags.parse_obj(data) == expected
