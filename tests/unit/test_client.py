from typing import Any, Callable
from unittest.mock import MagicMock
import httpx
import pytest
from pytest_mock import MockerFixture
from drav2_client.client import *
from drav2_client.exceptions import *
from drav2_client.models import *


class TestBaseClient:
    @pytest.mark.parametrize(
        "response, throwable",
        [
            (httpx.Response(200, request=httpx.Request("GET", "any")), None),
            (httpx.Response(201, request=httpx.Request("GET", "any")), None),
            (httpx.Response(204, request=httpx.Request("GET", "any")), None),
            (httpx.Response(400, request=httpx.Request("GET", "any")), BadRequest),
            (httpx.Response(401, request=httpx.Request("GET", "any")), Unauthorized),
            (httpx.Response(404, request=httpx.Request("GET", "any")), NotFound),
            (
                httpx.Response(402, request=httpx.Request("GET", "any")),
                UnknownHTTPError,
            ),
            (
                httpx.Response(500, request=httpx.Request("GET", "any")),
                InternalServerError,
            ),
        ],
    )
    def test__raise_for_status(
        self,
        response: httpx.Response,
        throwable: type[HTTPError],
        client: RegistryClient,
    ) -> None:
        if throwable:
            with pytest.raises(throwable):
                client._raise_for_status(response)
        else:
            client._raise_for_status(response)


class TestClient:
    def test_check_version(self, client: RegistryClient, mocker: MockerFixture) -> None:
        get_mock: MagicMock = mocker.patch.object(httpx.Client, "get")
        raise_status_mock: MagicMock = mocker.patch.object(
            RegistryClient, "_raise_for_status"
        )
        client.check_version()
        get_mock.assert_called_once_with(client.base_url, headers={})
        raise_status_mock.assert_called_once()

    @pytest.mark.parametrize(
        "expected",
        [
            RegistryResponse.construct(
                status_code=200,
                headers=Headers.construct(),
                body=Catalog.construct(repositories=["python", "mongo"]),
            ),
            RegistryResponse.construct(
                status_code=200,
                headers=Headers.construct(),
                body=Catalog.construct(repositories=[]),
            ),
            RegistryResponse.construct(
                status_code=401,
                headers=Headers.construct(),
                body=Errors.construct(
                    errors=[
                        Error.construct(
                            code="ABC",
                            message="Error",
                            detail=Detail.construct(name="python"),
                        )
                    ]
                ),
            ),
            RegistryResponse.construct(
                status_code=404,
                headers=Headers.construct(),
                body=Errors.construct(
                    errors=[
                        Error.construct(
                            code="ABC",
                            message="Error",
                            detail=Detail.construct(name="python"),
                        )
                    ]
                ),
            ),
            RegistryResponse.construct(
                status_code=500,
                headers=Headers.construct(),
                body=Errors.construct(
                    errors=[
                        Error.construct(
                            code="ABC",
                            message="Error",
                            detail=Detail.construct(name="python"),
                        )
                    ]
                ),
            ),
        ],
    )
    def test_get_catalog(
        self,
        expected: RegistryResponse,
        client: RegistryClient,
        get_patch: Callable[[Any], Any],
        mocker: MockerFixture,
    ) -> None:
        mocker.patch.object(
            httpx.Client,
            "get",
            get_patch(
                r"_catalog",
                dict_obj=expected.body.dict(by_alias=True),
                status_code=expected.status_code,
            ),
        )

        res: RegistryResponse = client.get_catalog()
        assert res == expected

    @pytest.mark.parametrize(
        "expected",
        [
            RegistryResponse.construct(
                status_code=200,
                headers=Headers.construct(),
                body=Tags.construct(name="python", tags=["latest"]),
            ),
            RegistryResponse.construct(
                status_code=200,
                headers=Headers.construct(),
                body=Tags.construct(name="python"),
            ),
            RegistryResponse.construct(
                status_code=401,
                headers=Headers.construct(),
                body=Errors.construct(
                    errors=[
                        Error.construct(
                            code="ABC",
                            message="Error",
                            detail=Detail.construct(name="python"),
                        )
                    ]
                ),
            ),
            RegistryResponse.construct(
                status_code=404,
                headers=Headers.construct(),
                body=Errors.construct(
                    errors=[
                        Error.construct(
                            code="ABC",
                            message="Error",
                            detail=Detail.construct(name="python"),
                        )
                    ]
                ),
            ),
            RegistryResponse.construct(
                status_code=500,
                headers=Headers.construct(),
                body=Errors.construct(
                    errors=[
                        Error.construct(
                            code="ABC",
                            message="Error",
                            detail=Detail.construct(name="python"),
                        )
                    ]
                ),
            ),
        ],
    )
    def test_get_tags(
        self,
        expected: RegistryResponse,
        client: RegistryClient,
        get_patch: Callable[[Any], Any],
        mocker: MockerFixture,
    ) -> None:
        mocker.patch.object(
            httpx.Client,
            "get",
            get_patch(
                r"\w+/tags/list",
                dict_obj=expected.body.dict(by_alias=True),
                status_code=expected.status_code,
            ),
        )

        res: RegistryResponse = client.get_tags("python")
        assert res == expected

    @pytest.mark.parametrize(
        "expected",
        [
            RegistryResponse.construct(
                status_code=200,
                headers=Headers.construct(),
                body=Manifest.construct(
                    schema_version=1,
                    name="python",
                    tag="latest",
                    architecture="amd64",
                    fs_layers=[FsLayer.construct(blob_sum="sha256:a3ed95caeb02ffe68c")],
                ),
            ),
            RegistryResponse.construct(
                status_code=200,
                headers=Headers.construct(),
                body=Manifest.construct(name="python", tag="latest"),
            ),
            RegistryResponse.construct(
                status_code=401,
                headers=Headers.construct(),
                body=Errors.construct(
                    errors=[
                        Error.construct(
                            code="ABC",
                            message="Error",
                            detail=Detail.construct(name="python"),
                        )
                    ]
                ),
            ),
            RegistryResponse.construct(
                status_code=404,
                headers=Headers.construct(),
                body=Errors.construct(
                    errors=[
                        Error.construct(
                            code="ABC",
                            message="Error",
                            detail=Detail.construct(name="python"),
                        )
                    ]
                ),
            ),
            RegistryResponse.construct(
                status_code=500,
                headers=Headers.construct(),
                body=Errors.construct(
                    errors=[
                        Error.construct(
                            code="ABC",
                            message="Error",
                            detail=Detail.construct(name="python"),
                        )
                    ]
                ),
            ),
        ],
    )
    def test_get_manifest(
        self,
        expected: RegistryResponse,
        client: RegistryClient,
        get_patch: Callable[[Any], Any],
        mocker: MockerFixture,
    ) -> None:
        mocker.patch.object(
            httpx.Client,
            "get",
            get_patch(
                r"\w+/manifests/\w+",
                dict_obj=expected.body.dict(by_alias=True),
                status_code=expected.status_code,
            ),
        )

        res: RegistryResponse = client.get_manifest(name="python", reference="latest")
        assert res == expected

    @pytest.mark.parametrize(
        "expected",
        [
            RegistryResponse.construct(
                status_code=200,
                headers=Headers.construct(),
                body=Blob.construct(content=b"hello world!"),
            ),
            RegistryResponse.construct(
                status_code=200,
                headers=Headers.construct(),
                body=Blob.construct(content=b""),
            ),
            RegistryResponse.construct(
                status_code=401,
                headers=Headers.construct(),
                body=Errors.construct(
                    errors=[
                        Error.construct(
                            code="ABC",
                            message="Error",
                            detail=Detail.construct(name="python"),
                        )
                    ]
                ),
            ),
            RegistryResponse.construct(
                status_code=404,
                headers=Headers.construct(),
                body=Errors.construct(
                    errors=[
                        Error.construct(
                            code="ABC",
                            message="Error",
                            detail=Detail.construct(name="python"),
                        )
                    ]
                ),
            ),
            RegistryResponse.construct(
                status_code=500,
                headers=Headers.construct(),
                body=Errors.construct(
                    errors=[
                        Error.construct(
                            code="ABC",
                            message="Error",
                            detail=Detail.construct(name="python"),
                        )
                    ]
                ),
            ),
        ],
    )
    def test_get_blob(
        self,
        expected: RegistryResponse,
        client: RegistryClient,
        get_patch: Callable[[Any], Any],
        mocker: MockerFixture,
    ) -> None:
        if isinstance(expected.body, Blob):
            patch: Callable[[Any], Any] = get_patch(
                r"\w+/blobs/\w+",
                bytes_obj=expected.body.content,
                status_code=expected.status_code,
            )
        else:
            patch: Callable[[Any], Any] = get_patch(
                r"\w+/blobs/\w+",
                dict_obj=expected.body.dict(),
                status_code=expected.status_code,
            )

        mocker.patch.object(httpx.Client, "get", patch)
        res: RegistryResponse = client.get_blob(name="any", digest="any")
        assert res == expected
