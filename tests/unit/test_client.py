from typing import Any, Callable
from unittest.mock import MagicMock
import httpx
import pytest
from pytest_mock import MockerFixture
from drav2_client.client import *
from drav2_client.exceptions import *
from drav2_client.models import *


class TestClient:
    def test_check_version(self, client: RegistryClient, mocker: MockerFixture) -> None:
        get_mock: MagicMock = mocker.patch.object(httpx.Client, "get")
        raise_status_mock: MagicMock = mocker.patch.object(
            RegistryClient, "_raise_for_status"
        )
        client.check_version()
        get_mock.assert_called_once_with(client.base_url, headers={})
        raise_status_mock.assert_called_once()

    def test_get_tags_list(
        self,
        client: RegistryClient,
        get_patch: Callable[[Any], Any],
        mocker: MockerFixture,
    ) -> None:
        expected: TagsList = TagsList.construct(name="python", tags=["latest"])
        mocker.patch.object(
            httpx.Client, "get", get_patch(r"\w+/tags/list", expected.dict())
        )
        res: TagsList = client.get_tags_list("python")
        assert res == expected

    @pytest.mark.parametrize(
        "status_code, expected, throwable",
        [
            (200, TagsList.construct(name="python", tags=["latest"]), None),
            (200, TagsList.construct(name="python"), None),
            (401, TagsList.construct(), Unauthorized),
            (404, TagsList.construct(), NotFound),
            (500, TagsList.construct(), InternalServerError),
        ],
    )
    def test_get_tags_list(
        self,
        status_code: int,
        expected: TagsList | None,
        throwable: type[HTTPError],
        client: RegistryClient,
        get_patch: Callable[[Any], Any],
        mocker: MockerFixture,
    ) -> None:
        mocker.patch.object(
            httpx.Client,
            "get",
            get_patch(
                r"\w+/tags/list", expected.dict(by_alias=True), status_code=status_code
            ),
        )

        if throwable:
            with pytest.raises(throwable):
                client.get_tags_list(expected.name)
        else:
            res: TagsList = client.get_tags_list(expected.name)
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
            (401, Manifest.construct(), Unauthorized),
            (404, Manifest.construct(), NotFound),
            (500, Manifest.construct(), InternalServerError),
        ],
    )
    def test_get_manifest(
        self,
        status_code: int,
        expected: TagsList | None,
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
                expected.dict(by_alias=True),
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
