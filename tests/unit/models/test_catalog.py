from typing import Any
from pydantic import ValidationError
import pytest
from drav2_client.models.catalog import Catalog


class TestCatalog:
    @pytest.mark.parametrize(
        "data, expected, throwable",
        [
            (
                {
                    "repositories": [
                        "python",
                        "debian",
                    ]
                },
                Catalog.construct(
                    repositories=[
                        "python",
                        "debian",
                    ]
                ),
                None,
            ),
            (
                {},
                Catalog.construct(repositories=[]),
                None,
            ),
            (
                {"repositories": None},
                Catalog.construct(repositories=[]),
                None,
            ),
            (
                {"repositories": "hello"},
                ("repositories",),
                ValidationError,
            ),
        ],
    )
    def test_init(
        self,
        data: dict[str, Any],
        expected: Catalog | tuple[str, ...],
        throwable: type[ValidationError] | None,
    ) -> None:
        if throwable:
            try:
                Catalog.parse_obj(data)
                raise AssertionError(f"Did not raise {throwable}")  # pragma: no cover
            except throwable as e:
                error_fields: list[str] = [wrapper._loc for wrapper in e.args[0]]
                assert sorted(error_fields) == sorted(expected)
        else:
            assert Catalog.parse_obj(data) == expected
