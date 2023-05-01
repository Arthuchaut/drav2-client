from typing import Any, Callable
from pydantic import ValidationError
import pytest

from drav2.models.client import Logins


class TestLogins:
    @pytest.mark.parametrize(
        "data, expected, throwable",
        [
            (
                {"user_id": "user_id", "password": "password"},
                Logins(user_id="user_id", password="password"),
                None,
            ),
            (
                {"user_id": None, "password": None},
                (".user_id", ".password"),
                ValidationError,
            ),
            (
                {"user_id": "", "password": ""},
                (".user_id", ".password"),
                ValidationError,
            ),
        ],
    )
    def test_init(
        self,
        data: dict[str, str],
        expected: Logins | tuple[str, ...],
        throwable: type[TypeError] | None,
        extract_error_list: Callable[[Any], Any],
        assert_sequences_equals: Callable[[Any], Any],
    ) -> None:
        if throwable:
            try:
                Logins.parse_obj(data)
                raise AssertionError(f"Did not raise {throwable}")  # pragma: no cover
            except throwable as e:
                error_list: list[str] = extract_error_list(e)
                assert_sequences_equals(error_list, expected)
        else:
            assert Logins.parse_obj(data) == expected
