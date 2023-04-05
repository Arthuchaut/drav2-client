import datetime
from typing import Any, Callable
from pydantic import ValidationError
import pytest
from drav2_client.models.errors import Detail, Error, Errors


class TestErrors:
    @pytest.mark.parametrize(
        "data, expected, throwable",
        [
            (
                {
                    "errors": [
                        {
                            "code": "MANIFEST_UNKNOWN",
                            "message": "Unknown manifest :(",
                            "detail": {
                                "name": "python",
                                "Tag": "latest",
                                "digest": "sha256:3e440a7045683e27f8e2fa0400",
                            },
                        }
                    ]
                },
                Errors.construct(
                    errors=[
                        Error.construct(
                            code=Error.Code.MANIFEST_UNKNOWN,
                            message="Unknown manifest :(",
                            detail=Detail.construct(
                                name="python",
                                tag="latest",
                                digest="sha256:3e440a7045683e27f8e2fa0400",
                            ),
                        )
                    ]
                ),
                None,
            ),
            (
                {
                    "errors": [
                        {
                            "code": None,
                            "message": None,
                            "detail": None,
                        },
                    ]
                },
                Errors.construct(
                    errors=[
                        Error.construct(
                            code=None,
                            message="",
                            detail=None,
                        )
                    ]
                ),
                None,
            ),
            (
                {
                    "errors": [
                        {
                            "detail": {
                                "name": None,
                                "tag": None,
                                "digest": None,
                            },
                        },
                    ]
                },
                Errors.construct(
                    errors=[
                        Error.construct(
                            code=None,
                            message="",
                            detail=Detail.construct(
                                name="",
                                tag="",
                                digest="",
                            ),
                        )
                    ]
                ),
                None,
            ),
            (
                {"errors": None},
                Errors.construct(errors=[]),
                None,
            ),
            (
                {
                    "errors": [
                        None,
                        # "", # Skiped 'cause of a weird Pydantic behaviour
                        12345,
                        # [], # Skiped 'cause of a weird Pydantic behaviour
                        {
                            "code": "ABC",
                            "message": [],
                            "detail": {
                                "name": {},
                                "Tag": [],
                                "digest": [],
                            },
                        },
                        {
                            "name": "python",
                            "Tag": "latest",
                            "digest": "sha256:3e440a7045683e27f8e2fa0400",
                        },
                    ]
                },
                (
                    ".errors[0]",
                    ".errors[1]",
                    ".errors[2].code",
                    ".errors[2].message",
                    ".errors[2].detail.name",
                    ".errors[2].detail.Tag",
                    ".errors[2].detail.digest",
                    ".errors[2].detail.digest",
                ),
                ValidationError,
            ),
        ],
    )
    def test_init(
        self,
        data: dict[str, Any],
        expected: Errors | tuple[str, ...],
        throwable: type[ValidationError] | None,
        extract_error_list: Callable[[Any], Any],
        assert_sequences_equals: Callable[[Any], Any],
    ) -> None:
        if throwable:
            try:
                Errors.parse_obj(data)
                raise AssertionError(f"Did not raise {throwable}")  # pragma: no cover
            except throwable as e:
                error_list: list[str] = extract_error_list(e)
                assert_sequences_equals(error_list, expected)
        else:
            assert Errors.parse_obj(data) == expected
