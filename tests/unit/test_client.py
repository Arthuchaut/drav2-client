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
        "status_code, expected, throwable",
        [
            (200, Catalog.construct(repositories=["python", "mongo"]), None),
            (200, Catalog.construct(repositories=[]), None),
            (401, Catalog.construct(), Unauthorized),
            (404, Catalog.construct(), NotFound),
            (500, Catalog.construct(), InternalServerError),
        ],
    )
    def test_get_catalog(
        self,
        status_code: int,
        expected: Manifest,
        throwable: type[HTTPError],
        client: RegistryClient,
        get_patch: Callable[[Any], Any],
        mocker: MockerFixture,
    ) -> None:
        mocker.patch.object(
            httpx.Client,
            "get",
            get_patch(
                r"_catalog",
                dict_obj=expected.dict(by_alias=True),
                status_code=status_code,
            ),
        )

        if throwable:
            with pytest.raises(throwable):
                client.get_catalog()
        else:
            res: Catalog = client.get_catalog()
            assert res == expected

    @pytest.mark.parametrize(
        "status_code, expected, throwable",
        [
            (200, Tags.construct(name="python", tags=["latest"]), None),
            (200, Tags.construct(name="python"), None),
            (401, Tags.construct(name="python"), Unauthorized),
            (404, Tags.construct(name="python"), NotFound),
            (500, Tags.construct(name="python"), InternalServerError),
        ],
    )
    def test_get_tags(
        self,
        status_code: int,
        expected: Tags,
        throwable: type[HTTPError],
        client: RegistryClient,
        get_patch: Callable[[Any], Any],
        mocker: MockerFixture,
    ) -> None:
        mocker.patch.object(
            httpx.Client,
            "get",
            get_patch(
                r"\w+/tags/list",
                dict_obj=expected.dict(by_alias=True),
                status_code=status_code,
            ),
        )

        if throwable:
            with pytest.raises(throwable):
                client.get_tags(expected.name)
        else:
            res: Tags = client.get_tags(expected.name)
            assert res == expected

    @pytest.mark.parametrize(
        "status_code, expected, throwable",
        [
            (
                200,
                Manifest.construct(
                    schema_version=1,
                    name="python",
                    tag="latest",
                    architecture="amd64",
                    fs_layers=[FsLayer.construct(blob_sum="sha256:a3ed95caeb02ffe68c")],
                ),
                None,
            ),
            (200, Manifest.construct(name="python", tag="latest"), None),
            (401, Manifest.construct(name="python", tag="latest"), Unauthorized),
            (404, Manifest.construct(name="python", tag="latest"), NotFound),
            (500, Manifest.construct(name="python", tag="latest"), InternalServerError),
        ],
    )
    def test_get_manifest(
        self,
        status_code: int,
        expected: Manifest,
        throwable: type[HTTPError],
        client: RegistryClient,
        get_patch: Callable[[Any], Any],
        mocker: MockerFixture,
    ) -> None:
        mocker.patch.object(
            httpx.Client,
            "get",
            get_patch(
                r"\w+/manifests/\w+",
                dict_obj=expected.dict(by_alias=True),
                status_code=status_code,
            ),
        )

        if throwable:
            with pytest.raises(throwable):
                client.get_manifest(name=expected.name, reference=expected.tag)
        else:
            res: Manifest = client.get_manifest(
                name=expected.name, reference=expected.tag
            )
            assert res == expected

    @pytest.mark.parametrize(
        "status_code, expected, throwable",
        [
            (200, b"hello world!", None),
            (200, b"", None),
            (401, b"", Unauthorized),
            (404, b"", NotFound),
            (500, b"", InternalServerError),
        ],
    )
    def test_get_blob(
        self,
        status_code: int,
        expected: bytes,
        throwable: type[HTTPError],
        client: RegistryClient,
        get_patch: Callable[[Any], Any],
        mocker: MockerFixture,
    ) -> None:
        mocker.patch.object(
            httpx.Client,
            "get",
            get_patch(r"\w+/blobs/\w+", bytes_obj=expected, status_code=status_code),
        )

        if throwable:
            with pytest.raises(throwable):
                client.get_blob(name="any", digest="any")
        else:
            res: bytes = client.get_blob(name="any", digest="any")
            assert res == expected
