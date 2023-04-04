from typing import Any
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
                ("name", "tags"),
                ValidationError,
            ),
        ],
    )
    def test_init(
        self,
        data: dict[str, Any],
        expected: Tags | tuple[str, ...],
        throwable: type[ValidationError] | None,
    ) -> None:
        if throwable:
            try:
                Tags.parse_obj(data)
                raise AssertionError(f"Did not raise {throwable}")  # pragma: no cover
            except throwable as e:
                error_fields: list[str] = [wrapper._loc for wrapper in e.args[0]]
                assert sorted(error_fields) == sorted(expected)
        else:
            assert Tags.parse_obj(data) == expected
