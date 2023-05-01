import pytest
from drav2_client.models.blob import Blob, UnreadableError
from conftest import MockedResponse


class TestBlob:
    @pytest.mark.parametrize(
        "obj, expected, throwable",
        [
            (
                Blob(
                    res=MockedResponse(status_code=200, headers={}, text="hello world!")
                ),
                b"hello world!",
                None,
            ),
            (
                Blob(res=MockedResponse(status_code=200, headers={}, text="")),
                b"",
                None,
            ),
            (
                Blob(
                    res=MockedResponse(
                        status_code=200,
                        headers={},
                        text="hello world!",
                        stream_mode=True,
                    )
                ),
                b"hello world!",
                UnreadableError,
            ),
        ],
    )
    def test_access_bytes(
        self, obj: Blob, expected: bytes | None, throwable: type[UnreadableError] | None
    ) -> None:
        if throwable:
            with pytest.raises(throwable):
                obj.content
        else:
            assert obj.content == expected

        assert b"".join([*obj.iter_bytes()]) == expected
