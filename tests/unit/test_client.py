import json
from typing import Any, Callable, Iterator
import warnings
import httpx
from pydantic import BaseModel
import pytest
from pytest_mock import MockerFixture
from conftest import _FAKE_BASE_URL
from drav2_client.client import *
from drav2_client.models import *
from drav2_client.types import MediaType
from conftest import MockedResponse


class TestBaseClient:
    @pytest.mark.parametrize(
        "res, model, from_bytes",
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
                    headers={"Link": '</uri/path/?last=python&n=10>; rel="next"'},
                    text=json.dumps({"repositories": ["python", "debian"]}),
                    request=None,
                ),
                Catalog,
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
        from_bytes: bool,
        client: RegistryClient,
        mocker: MockerFixture,
    ) -> None:
        expected: RegistryResponse = RegistryResponse(
            status_code=res.status_code, headers=Headers.parse_obj(res.headers)
        )

        if res.status_code >= 500:
            expected.body = Errors(errors=[Error(code=Error.Code.INTERNAL_ERROR)])
        elif res.status_code >= 400:
            expected.body = Errors.parse_obj(res.json())
        elif model:
            if from_bytes:
                expected.body = model(res=res)
            else:
                expected.body = model.parse_obj(res.json())

        res: RegistryResponse = client._build_response(
            res, model=model, from_bytes=from_bytes
        )
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
                            detail=dict(name="python"),
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
                            detail=dict(name="python"),
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
                            detail=dict(name="python"),
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
                            detail=dict(name="python"),
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
                body=ManifestV2(
                    schemaVersion=2,
                    config=Config(
                        media_type="application/vnd.docker.container.image.v1+json"
                    ),
                    layers=[
                        Layer(
                            media_type="application/vnd.docker.image.rootfs.diff.tar.gzip",
                            size=55045608,
                            digest="sha256:54e726b437fb92dd7b43f4dd5cd79b01a1e96a22849b2fc2ffeb34fac2d65440",
                        )
                    ],
                ),
            ),
            RegistryResponse(
                status_code=200,
                headers=Headers(),
                body=ManifestV1(schemaVersion=1, name="python", tag="latest"),
            ),
            RegistryResponse(
                status_code=200,
                headers=Headers(),
                body=ManifestV2(),
            ),
            RegistryResponse(
                status_code=401,
                headers=Headers(),
                body=Errors(
                    errors=[
                        Error(
                            code="INTERNAL_ERROR",
                            message="Error",
                            detail=dict(name="python"),
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
                            detail=dict(name="python"),
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
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            mocker.patch.object(
                httpx.Client,
                "get",
                request_patch(
                    r"\w+/manifests/\w+",
                    dict_obj=expected.body.dict(by_alias=True),
                    status_code=expected.status_code,
                ),
            )

            if version := getattr(expected.body, "schema_version", None):
                media_type: MediaType = (
                    MediaType.SIGNED_MANIFEST_V1
                    if version == 1
                    else MediaType.MANIFEST_V2
                )
                res: RegistryResponse = client.get_manifest(
                    name="python", reference="latest", media_type=media_type
                )
            else:
                res: RegistryResponse = client.get_manifest(
                    name="python", reference="latest"
                )

            assert res == expected

    @pytest.mark.parametrize(
        "stream, expected",
        [
            (
                False,
                RegistryResponse(
                    status_code=200,
                    headers=Headers(),
                    body=Blob(
                        res=MockedResponse(
                            status_code=200, headers={}, text="hello world!"
                        )
                    ),
                ),
            ),
            (
                True,
                RegistryResponse(
                    status_code=200,
                    headers=Headers(),
                    body=Blob(
                        res=MockedResponse(
                            status_code=200,
                            headers={},
                            text="hello world!",
                            stream_mode=True,
                        )
                    ),
                ),
            ),
            (
                False,
                RegistryResponse(
                    status_code=401,
                    headers=Headers(),
                    body=Errors(
                        errors=[
                            Error(
                                code="INTERNAL_ERROR",
                                message="Error",
                                detail=dict(name="python"),
                            )
                        ]
                    ),
                ),
            ),
            (
                True,
                RegistryResponse(
                    status_code=401,
                    headers=Headers(),
                    body=Errors(
                        errors=[
                            Error(
                                code="INTERNAL_ERROR",
                                message="Error",
                                detail=dict(name="python"),
                            )
                        ]
                    ),
                ),
            ),
            (
                False,
                RegistryResponse(
                    status_code=404,
                    headers=Headers(),
                    body=Errors(
                        errors=[
                            Error(
                                code="INTERNAL_ERROR",
                                message="Error",
                                detail=dict(name="python"),
                            )
                        ]
                    ),
                ),
            ),
            (
                False,
                RegistryResponse(
                    status_code=500,
                    headers=Headers(),
                    body=Errors(errors=[Error(code="INTERNAL_ERROR")]),
                ),
            ),
        ],
    )
    def test_get_blob(
        self,
        stream: bool,
        expected: RegistryResponse,
        client: RegistryClient,
        send_patch: Callable[[Any], Any],
        mocker: MockerFixture,
    ) -> None:
        if isinstance(expected.body, Blob):
            patch: Callable[[Any], Any] = send_patch(
                r"\w+/blobs/\w+",
                bytes_obj=b"hello world!",
                status_code=expected.status_code,
            )
        else:
            patch: Callable[[Any], Any] = send_patch(
                r"\w+/blobs/\w+",
                dict_obj=expected.body.dict(),
                status_code=expected.status_code,
            )

        mocker.patch.object(httpx.Client, "send", patch)
        res: RegistryResponse = client.get_blob(
            name="any",
            digest="sha256:54e726b437fb92dd7b43f4dd5cd79b01a1e96a22849b2fc2ffeb34fac2d65440",
            stream=stream,
        )
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
                            detail=dict(name="python"),
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
                            detail=dict(name="python"),
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

    @pytest.mark.parametrize(
        "expected",
        [
            RegistryResponse(
                status_code=201,
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
                            detail=dict(name="python"),
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
                            detail=dict(name="python"),
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
                            code="NAME_UNKNOWN",
                            message="Error",
                            detail=dict(name="python"),
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
    def test_put_manifest(
        self,
        expected: RegistryResponse,
        client: RegistryClient,
        request_patch: Callable[[Any], Any],
        mocker: MockerFixture,
    ) -> None:
        if expected.status_code is RegistryResponse.Status.CREATED:
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

        mocker.patch.object(httpx.Client, "put", patch)
        res: RegistryResponse = client.put_manifest(
            name="python", reference="latest", manifest=ManifestV2.construct()
        )
        assert res == expected

    @pytest.mark.parametrize(
        "name, digest, throwable",
        [
            (
                "any",
                "sha256:54e726b437fb92dd7b43f4dd5cd79b01a1e96a22849b2fc2ffeb34fac2d65440",
                None,
            ),
            (
                "any",
                "wrong_digest",
                ValueError,
            ),
        ],
    )
    def test_delete_blob(
        self,
        name: str,
        digest: str,
        throwable: type[ValueError] | None,
        client: RegistryClient,
        request_patch: Callable[[Any], Any],
        mocker: MockerFixture,
    ) -> None:
        patch: Callable[[Any], Any] = request_patch(r"\w+/blobs/\w+", status_code=200)
        mocker.patch.object(httpx.Client, "delete", patch)

        if throwable:
            with pytest.raises(throwable):
                client.delete_blob(name, digest)
        else:
            res: RegistryResponse = client.delete_blob(name, digest)
            assert res.status_code is RegistryResponse.Status.OK

    @pytest.mark.parametrize(
        "expected",
        [
            RegistryResponse(
                status_code=201,
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
                            detail=dict(name="python"),
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
                            detail=dict(name="python"),
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
                            code="NAME_UNKNOWN",
                            message="Error",
                            detail=dict(name="python"),
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
    def test_initiate_blob_upload(
        self,
        expected: RegistryResponse,
        client: RegistryClient,
        request_patch: Callable[[Any], Any],
        mocker: MockerFixture,
    ) -> None:
        if expected.status_code is RegistryResponse.Status.CREATED:
            patch: Callable[[Any], Any] = request_patch(
                r"\w+/blobs/uploads/",
                status_code=expected.status_code,
            )
        else:
            patch: Callable[[Any], Any] = request_patch(
                r"\w+/blobs/uploads/",
                dict_obj=expected.body.dict(by_alias=True),
                status_code=expected.status_code,
            )

        mocker.patch.object(httpx.Client, "post", patch)
        res: RegistryResponse = client.initiate_blob_upload(
            name="python",
            data=b"content",
            digest="sha256:54e726b437fb92dd7b43f4dd5cd79b01a1e96a22849b2fc2ffeb34fac2d65440",
        )
        assert res == expected

    @pytest.mark.parametrize(
        "expected",
        [
            RegistryResponse(
                status_code=204,
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
                            detail=dict(name="python"),
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
                            detail=dict(name="python"),
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
                            code="NAME_UNKNOWN",
                            message="Error",
                            detail=dict(name="python"),
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
    def test_get_blob_upload(
        self,
        expected: RegistryResponse,
        client: RegistryClient,
        request_patch: Callable[[Any], Any],
        mocker: MockerFixture,
    ) -> None:
        if expected.status_code is RegistryResponse.Status.NO_CONTENT:
            patch: Callable[[Any], Any] = request_patch(
                r"\w+/blobs/uploads/[a-zA-Z0-9-_.=]+",
                status_code=expected.status_code,
            )
        else:
            patch: Callable[[Any], Any] = request_patch(
                r"\w+/blobs/uploads/[a-zA-Z0-9-_.=]+",
                dict_obj=expected.body.dict(by_alias=True),
                status_code=expected.status_code,
            )

        mocker.patch.object(httpx.Client, "get", patch)
        res: RegistryResponse = client.get_blob_upload(
            name="python", uuid="abcd-efgh-ijkl-mnop"
        )
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
                            detail=dict(name="python"),
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
                            detail=dict(name="python"),
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
                            code="NAME_UNKNOWN",
                            message="Error",
                            detail=dict(name="python"),
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
    def test_patch_blob_upload(
        self,
        expected: RegistryResponse,
        client: RegistryClient,
        request_patch: Callable[[Any], Any],
        mocker: MockerFixture,
    ) -> None:
        if expected.status_code is RegistryResponse.Status.ACCEPTED:
            patch: Callable[[Any], Any] = request_patch(
                r"\w+/blobs/uploads/[a-zA-Z0-9-_.=]+",
                status_code=expected.status_code,
            )
        else:
            patch: Callable[[Any], Any] = request_patch(
                r"\w+/blobs/uploads/[a-zA-Z0-9-_.=]+",
                dict_obj=expected.body.dict(by_alias=True),
                status_code=expected.status_code,
            )

        mocker.patch.object(httpx.Client, "patch", patch)
        res: RegistryResponse = client.patch_blob_upload(
            name="python", uuid="abcd-efgh-ijkl-mnop", data=b"content"
        )
        assert res == expected

    @pytest.mark.parametrize(
        "expected",
        [
            RegistryResponse(
                status_code=201,
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
                            detail=dict(name="python"),
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
                            detail=dict(name="python"),
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
                            code="NAME_UNKNOWN",
                            message="Error",
                            detail=dict(name="python"),
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
    def test_complete_blob_upload(
        self,
        expected: RegistryResponse,
        client: RegistryClient,
        request_patch: Callable[[Any], Any],
        mocker: MockerFixture,
    ) -> None:
        if expected.status_code is RegistryResponse.Status.CREATED:
            patch: Callable[[Any], Any] = request_patch(
                r"\w+/blobs/uploads/[a-zA-Z0-9-_.=]+",
                status_code=expected.status_code,
            )
        else:
            patch: Callable[[Any], Any] = request_patch(
                r"\w+/blobs/uploads/[a-zA-Z0-9-_.=]+",
                dict_obj=expected.body.dict(by_alias=True),
                status_code=expected.status_code,
            )

        mocker.patch.object(httpx.Client, "put", patch)
        res: RegistryResponse = client.complete_blob_upload(
            name="python",
            uuid="abcd-efgh-ijkl-mnop",
            digest="sha256:54e726b437fb92dd7b43f4dd5cd79b01a1e96a22849b2fc2ffeb34fac2d65440",
            data=b"content",
        )
        assert res == expected

    @pytest.mark.parametrize(
        "expected",
        [
            RegistryResponse(
                status_code=204,
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
                            detail=dict(name="python"),
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
                            detail=dict(name="python"),
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
                            code="NAME_UNKNOWN",
                            message="Error",
                            detail=dict(name="python"),
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
    def test_cancel_blob_upload(
        self,
        expected: RegistryResponse,
        client: RegistryClient,
        request_patch: Callable[[Any], Any],
        mocker: MockerFixture,
    ) -> None:
        if expected.status_code is RegistryResponse.Status.NO_CONTENT:
            patch: Callable[[Any], Any] = request_patch(
                r"\w+/blobs/uploads/[a-zA-Z0-9-_.=]+",
                status_code=expected.status_code,
            )
        else:
            patch: Callable[[Any], Any] = request_patch(
                r"\w+/blobs/uploads/[a-zA-Z0-9-_.=]+",
                dict_obj=expected.body.dict(by_alias=True),
                status_code=expected.status_code,
            )

        mocker.patch.object(httpx.Client, "delete", patch)
        res: RegistryResponse = client.cancel_blob_upload(
            name="python", uuid="abcd-efgh-ijkl-mnop"
        )
        assert res == expected

    def test_location_go(
        self,
        client: RegistryClient,
        request_patch: Callable[[Any], Any],
        mocker: MockerFixture,
    ) -> None:
        patch: Callable[[Any], Any] = request_patch(r".+", status_code=200)
        mocker.patch.object(httpx.Client, "get", patch)
        expected_res: RegistryResponse = RegistryResponse(
            status_code=200, headers=Headers()
        )
        initial_res: RegistryResponse = RegistryResponse.construct(
            headers=Headers.construct(
                location=Location(
                    url="http://fake_host/v2/path/to/my/resource/?key=val",
                )
            )
        )
        initial_res.headers.location._client = client
        location_res: RegistryResponse = initial_res.headers.location.go()
        assert location_res == expected_res
