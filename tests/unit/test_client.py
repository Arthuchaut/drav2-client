import json
from typing import Any, Callable
from unittest.mock import MagicMock
import httpx
from pydantic import BaseModel
import pytest
from pytest_mock import MockerFixture
from conftest import _FAKE_BASE_URL
from drav2_client.client import *
from drav2_client.models import *


class TestBaseClient:
    @pytest.mark.parametrize(
        "res, model, from_content",
        [
            (
                httpx.Response(
                    200,
                    headers={"date": "Sat, 01 Apr 2023 23:18:26 GMT"},
                    text=json.dumps({"name": "python", "tags": ["latest", "3.11"]}),
                    request=None,
                ),
                Tags,
                False,
            ),
            (
                httpx.Response(
                    200,
                    headers={"date": "Sat, 01 Apr 2023 23:18:26 GMT"},
                    content=b"Hello!",
                    request=None,
                ),
                Blob,
                True,
            ),
            (
                httpx.Response(
                    200,
                    headers={"content-type": "hello world!"},
                    text=json.dumps({"name": "python", "tags": ["latest", "3.11"]}),
                    request=None,
                ),
                None,
                False,
            ),
            (
                httpx.Response(
                    404,
                    headers={"content-type": "hello world!"},
                    text=json.dumps({"errors": [{"code": "MANIFEST_UNKNOWN"}]}),
                    request=None,
                ),
                None,
                False,
            ),
            (
                httpx.Response(
                    502,
                    headers={"content-type": "hello world!"},
                    request=None,
                ),
                None,
                False,
            ),
        ],
    )
    def test__build_response(
        self,
        res: httpx.Response,
        model: type[BaseModel] | None,
        from_content: bool,
        client: RegistryClient,
    ) -> None:
        expected: RegistryResponse = RegistryResponse(
            status_code=res.status_code, headers=Headers.parse_obj(res.headers)
        )

        if res.status_code >= 500:
            expected.body = Errors(errors=[Error(code=Error.Code.INTERNAL_ERROR)])
        elif res.status_code >= 400:
            expected.body = Errors.parse_obj(res.json())
        elif model:
            if from_content:
                expected.body = model(content=res.content)
            else:
                expected.body = model.parse_obj(res.json())

        res: RegistryResponse = client._build_response(res, model, from_content)
        assert res == expected

    @pytest.mark.parametrize(
        "user_id, password, expected",
        [
            ("user", "password", {"Authorization": "Basic dXNlcjpwYXNzd29yZA=="}),
            ("", "", {}),
            (None, None, {}),
        ],
    )
    def test__auth_client_property(
        self, user_id: str | None, password: str | None, expected: dict[str, str]
    ) -> None:
        client: RegistryClient = RegistryClient(
            _FAKE_BASE_URL, user_id=user_id, password=password
        )
        assert client._auth_header == expected


class TestClient:
    def test_check_version(
        self,
        client: RegistryClient,
        request_patch: Callable[[Any], Any],
        mocker: MockerFixture,
    ) -> None:
        mocker.patch.object(httpx.Client, "get", request_patch(r"", status_code=200))
        res: RegistryResponse = client.check_version()
        assert res.status_code is RegistryResponse.Status.OK

    @pytest.mark.parametrize(
        "expected",
        [
            RegistryResponse(
                status_code=200,
                headers=Headers(),
                body=Catalog(repositories=["python", "mongo"]),
            ),
            RegistryResponse(
                status_code=200,
                headers=Headers(),
                body=Catalog(repositories=[]),
            ),
            RegistryResponse(
                status_code=401,
                headers=Headers(),
                body=Errors(
                    errors=[
                        Error(
                            code="INTERNAL_ERROR",
                            message="Error",
                            detail=Detail(name="python"),
                        )
                    ]
                ),
            ),
            RegistryResponse(
                status_code=404,
                headers=Headers(),
                body=Errors(
                    errors=[
                        Error(
                            code="INTERNAL_ERROR",
                            message="Error",
                            detail=Detail(name="python"),
                        )
                    ]
                ),
            ),
            RegistryResponse(
                status_code=500,
                headers=Headers(),
                body=Errors(errors=[Error(code="INTERNAL_ERROR")]),
            ),
        ],
    )
    def test_get_catalog(
        self,
        expected: RegistryResponse,
        client: RegistryClient,
        request_patch: Callable[[Any], Any],
        mocker: MockerFixture,
    ) -> None:
        mocker.patch.object(
            httpx.Client,
            "get",
            request_patch(
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
            RegistryResponse(
                status_code=200,
                headers=Headers(),
                body=Tags(name="python", tags=["latest"]),
            ),
            RegistryResponse(
                status_code=200,
                headers=Headers(),
                body=Tags(name="python"),
            ),
            RegistryResponse(
                status_code=401,
                headers=Headers(),
                body=Errors(
                    errors=[
                        Error(
                            code="INTERNAL_ERROR",
                            message="Error",
                            detail=Detail(name="python"),
                        )
                    ]
                ),
            ),
            RegistryResponse(
                status_code=404,
                headers=Headers(),
                body=Errors(
                    errors=[
                        Error(
                            code="INTERNAL_ERROR",
                            message="Error",
                            detail=Detail(name="python"),
                        )
                    ]
                ),
            ),
            RegistryResponse(
                status_code=500,
                headers=Headers(),
                body=Errors(errors=[Error(code="INTERNAL_ERROR")]),
            ),
        ],
    )
    def test_get_tags(
        self,
        expected: RegistryResponse,
        client: RegistryClient,
        request_patch: Callable[[Any], Any],
        mocker: MockerFixture,
    ) -> None:
        mocker.patch.object(
            httpx.Client,
            "get",
            request_patch(
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
            RegistryResponse(
                status_code=200,
                headers=Headers(),
                body=Manifest(
                    schema_version=2,
                    config=Config(
                        media_type="application/vnd.docker.container.image.v1+json"
                    ),
                    layers=[
                        Layer(
                            media_type="pplication/vnd.docker.image.rootfs.diff.tar.gzip",
                            size=55045608,
                            digest="sha256:3e440a7045683e27f8e2fa04000e0e078d8dfac0c971358ae0f8c65c13321c8e",
                        )
                    ],
                ),
            ),
            RegistryResponse(
                status_code=200,
                headers=Headers(),
                body=Manifest(schema_version=2),
            ),
            RegistryResponse(
                status_code=401,
                headers=Headers(),
                body=Errors(
                    errors=[
                        Error(
                            code="INTERNAL_ERROR",
                            message="Error",
                            detail=Detail(name="python"),
                        )
                    ]
                ),
            ),
            RegistryResponse(
                status_code=404,
                headers=Headers(),
                body=Errors(
                    errors=[
                        Error(
                            code="INTERNAL_ERROR",
                            message="Error",
                            detail=Detail(name="python"),
                        )
                    ]
                ),
            ),
            RegistryResponse(
                status_code=500,
                headers=Headers(),
                body=Errors(errors=[Error(code="INTERNAL_ERROR")]),
            ),
        ],
    )
    def test_get_manifest(
        self,
        expected: RegistryResponse,
        client: RegistryClient,
        request_patch: Callable[[Any], Any],
        mocker: MockerFixture,
    ) -> None:
        mocker.patch.object(
            httpx.Client,
            "get",
            request_patch(
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
            RegistryResponse(
                status_code=200,
                headers=Headers(),
                body=Blob(content=b"hello world!"),
            ),
            RegistryResponse(
                status_code=200,
                headers=Headers(),
                body=Blob(content=b""),
            ),
            RegistryResponse(
                status_code=401,
                headers=Headers(),
                body=Errors(
                    errors=[
                        Error(
                            code="INTERNAL_ERROR",
                            message="Error",
                            detail=Detail(name="python"),
                        )
                    ]
                ),
            ),
            RegistryResponse(
                status_code=404,
                headers=Headers(),
                body=Errors(
                    errors=[
                        Error(
                            code="INTERNAL_ERROR",
                            message="Error",
                            detail=Detail(name="python"),
                        )
                    ]
                ),
            ),
            RegistryResponse(
                status_code=500,
                headers=Headers(),
                body=Errors(errors=[Error(code="INTERNAL_ERROR")]),
            ),
        ],
    )
    def test_get_blob(
        self,
        expected: RegistryResponse,
        client: RegistryClient,
        request_patch: Callable[[Any], Any],
        mocker: MockerFixture,
    ) -> None:
        if isinstance(expected.body, Blob):
            patch: Callable[[Any], Any] = request_patch(
                r"\w+/blobs/\w+",
                bytes_obj=expected.body.content,
                status_code=expected.status_code,
            )
        else:
            patch: Callable[[Any], Any] = request_patch(
                r"\w+/blobs/\w+",
                dict_obj=expected.body.dict(),
                status_code=expected.status_code,
            )

        mocker.patch.object(httpx.Client, "get", patch)
        res: RegistryResponse = client.get_blob(name="any", digest="any")
        assert res == expected

    @pytest.mark.parametrize(
        "expected",
        [
            RegistryResponse(
                status_code=202,
                headers=Headers(),
                body=None,
            ),
            RegistryResponse(
                status_code=400,
                headers=Headers(),
                body=Errors(
                    errors=[
                        Error(
                            code="NAME_INVALID",
                            message="Error",
                            detail=Detail(name="python"),
                        )
                    ]
                ),
            ),
            RegistryResponse(
                status_code=401,
                headers=Headers(),
                body=Errors(
                    errors=[
                        Error(
                            code="UNAUTHORIZED",
                            message="Error",
                            detail=Detail(name="python"),
                        )
                    ]
                ),
            ),
            RegistryResponse(
                status_code=500,
                headers=Headers(),
                body=Errors(errors=[Error(code="INTERNAL_ERROR")]),
            ),
        ],
    )
    def test_delete_manifest(
        self,
        expected: RegistryResponse,
        client: RegistryClient,
        request_patch: Callable[[Any], Any],
        mocker: MockerFixture,
    ) -> None:
        if expected.status_code is RegistryResponse.Status.ACCEPTED:
            patch: Callable[[Any], Any] = request_patch(
                r"\w+/manifests/\w+",
                status_code=expected.status_code,
            )
        else:
            patch: Callable[[Any], Any] = request_patch(
                r"\w+/manifests/\w+",
                dict_obj=expected.body.dict(by_alias=True),
                status_code=expected.status_code,
            )

        mocker.patch.object(httpx.Client, "delete", patch)
        res: RegistryResponse = client.delete_manifest(
            name="python", reference="latest"
        )
        assert res == expected
