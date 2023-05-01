from typing import Any, Callable
from pydantic import ValidationError
import pytest
from drav2.models.catalog import Catalog


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
                (".repositories",),
                ValidationError,
            ),
        ],
    )
    def test_init(
        self,
        data: dict[str, Any],
        expected: Catalog | tuple[str, ...],
        throwable: type[ValidationError] | None,
        extract_error_list: Callable[[Any], Any],
        assert_sequences_equals: Callable[[Any], Any],
    ) -> None:
        if throwable:
            try:
                Catalog.parse_obj(data)
                raise AssertionError(f"Did not raise {throwable}")  # pragma: no cover
            except throwable as e:
                error_list: list[str] = extract_error_list(e)
                assert_sequences_equals(error_list, expected)
        else:
            assert Catalog.parse_obj(data) == expected
