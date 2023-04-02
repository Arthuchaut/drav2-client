import base64
from functools import cached_property
import json
from typing import Optional
from urllib.parse import urljoin
import httpx
from pydantic import BaseModel
from drav2_client.types import AnyTransport
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
    def check_version(self) -> None:
        res: httpx.Response = self._client.get(self.base_url, headers=self._auth_header)
        return self._build_response(res)

    def get_catalog(self) -> RegistryResponse:
        # Add pagination management from Link
        # GET /v2/_catalog?n=<n from the request>&last=<last repository value from previous response>
        url: str = urljoin(self.base_url, "_catalog")
        res: httpx.Response = self._client.get(url, headers=self._auth_header)
        return self._build_response(res, Catalog)

    def get_tags(self, name: str) -> RegistryResponse:
        # Add pagination management from Link
        # GET /v2/<name>/tags/list?n=<n from the request>&last=<last tag value from previous response>
        url: str = urljoin(self.base_url, f"{name}/tags/list")
        res: httpx.Response = self._client.get(url, headers=self._auth_header)
        return self._build_response(res, Tags)

    def get_manifest(self, name: str, reference: str) -> RegistryResponse:
        url: str = urljoin(self.base_url, f"{name}/manifests/{reference}")
        res: httpx.Response = self._client.get(url, headers=self._auth_header)
        return self._build_response(res, Manifest)

    def get_blob(self, name: str, digest: str) -> RegistryResponse:
        url: str = urljoin(self.base_url, f"{name}/blobs/{digest}")
        res: httpx.Response = self._client.get(url, headers=self._auth_header)
        return self._build_response(res, Blob, from_content=True)
