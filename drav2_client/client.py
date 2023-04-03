import base64
import enum
from functools import cached_property
import json
from typing import ClassVar, Literal, Optional
from urllib.parse import urljoin
import httpx
from pydantic import BaseModel
from drav2_client.types import AnyTransport, ManifestMediaType
from drav2_client.models import *

__all__: list[str] = [
    "RegistryClient",
]


class _BaseClient:
    def __init__(
        self,
        base_url: str,
        user_id: Optional[str] = None,
        password: Optional[str] = None,
        transport: Optional[AnyTransport] = None,
    ) -> None:
        self.base_url: str = base_url
        self._client: httpx.Client = httpx.Client(transport=transport)
        self._user_id: str | None = user_id
        self._password: str | None = password

    @cached_property
    def _auth_header(self) -> dict[str, str]:
        if self._user_id and self._password:
            fmt: str = f"{self._user_id}:{self._password}"
            basic: str = base64.b64encode(fmt.encode("utf8")).decode("utf8")
            return {"Authorization": f"Basic {basic}"}

        return {}

    def _build_response(
        self,
        res: httpx.Response,
        model: Optional[type[BaseModel]] = None,
        from_content: Optional[bool] = False,
    ) -> RegistryResponse:
        result: BaseModel | None = None

        if res.status_code >= 500:
            result = Errors(errors=[Error(code=Error.Code.INTERNAL_ERROR)])
        elif res.status_code >= 400:
            result = Errors.parse_obj(res.json())
        elif model:
            if from_content:
                result = model(content=res.content)
            else:
                result = model.parse_obj(res.json())

        return RegistryResponse(
            status_code=res.status_code,
            headers=Headers.parse_obj(res.headers),
            body=result,
        )


class RegistryClient(_BaseClient):
    _DEFAULT_RESULT_SIZE: ClassVar[int] = 10

    def check_version(self) -> RegistryResponse:
        res: httpx.Response = self._client.get(self.base_url, headers=self._auth_header)
        return self._build_response(res)

    def get_catalog(
        self, *, size: Optional[int] = _DEFAULT_RESULT_SIZE, last: Optional[str] = ""
    ) -> RegistryResponse:
        url: str = urljoin(self.base_url, "_catalog")
        res: httpx.Response = self._client.get(
            url, params=dict(n=size, last=last), headers=self._auth_header
        )
        return self._build_response(res, Catalog)

    def get_tags(
        self,
        name: str,
        *,
        size: Optional[int] = _DEFAULT_RESULT_SIZE,
        last: Optional[str] = "",
    ) -> RegistryResponse:
        url: str = urljoin(self.base_url, f"{name}/tags/list")
        res: httpx.Response = self._client.get(
            url, params=dict(n=size, last=last), headers=self._auth_header
        )
        return self._build_response(res, Tags)

    def get_manifest(
        self,
        name: str,
        reference: str,
        *,
        media_type: Optional[ManifestMediaType] = ManifestMediaType.V2,
    ) -> RegistryResponse:
        url: str = urljoin(self.base_url, f"{name}/manifests/{reference}")
        headers: dict[str, str] = self._auth_header
        headers |= {"Accept": media_type}
        res: httpx.Response = self._client.get(url, headers=headers)
        model: type[BaseModel] = ManifestV2

        if media_type is ManifestMediaType.V1:
            model = ManifestV1

        return self._build_response(res, model)

    def get_blob(self, name: str, digest: str) -> RegistryResponse:
        url: str = urljoin(self.base_url, f"{name}/blobs/{digest}")
        res: httpx.Response = self._client.get(url, headers=self._auth_header)
        return self._build_response(res, Blob, from_content=True)

    def delete_manifest(self, name: str, reference: str) -> RegistryResponse:
        url: str = urljoin(self.base_url, f"{name}/manifests/{reference}")
        headers: dict[str, str] = self._auth_header
        res: httpx.Response = self._client.delete(url, headers=headers)
        return self._build_response(res)
