import base64
from functools import cached_property
import json
from typing import Optional
from urllib.parse import urljoin
import httpx
from pydantic import BaseModel
from drav2_client.types import AnyTransport
from drav2_client.exceptions import *
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

    def _raise_for_status(self, res: httpx.Response) -> None:
        try:
            res.raise_for_status()
        except httpx.HTTPStatusError as e:
            if res.status_code == 400:
                raise BadRequest(e)
            elif res.status_code == 401:
                raise Unauthorized(e)
            elif res.status_code == 404:
                raise NotFound(e)
            elif res.status_code >= 500:
                raise InternalServerError(e)
            else:
                raise UnknownHTTPError(e)

    def _build_response(
        self,
        res: httpx.Response,
        model: type[BaseModel],
        from_content: Optional[bool] = False,
    ) -> RegistryResponse:
        if from_content:
            result: BaseModel = model.construct(content=res.content)
        else:
            result: BaseModel = model.parse_obj(res.json())

        return RegistryResponse.construct(
            status_code=res.status_code,
            headers=Headers.parse_obj(res.headers),
            result=result,
        )

    @cached_property
    def _auth_header(self) -> dict[str, str]:
        if self._user_id and self._password:
            fmt: str = f"{self._user_id}:{self._password}"
            basic: str = base64.b64encode(fmt.encode("utf8")).decode("utf8")
            return {"Authorization": f"Basic {basic}"}

        return {}


class RegistryClient(_BaseClient):
    def check_version(self) -> None:
        res: httpx.Response = self._client.get(self.base_url, headers=self._auth_header)
        self._raise_for_status(res)

    def get_catalog(self) -> RegistryResponse:
        url: str = urljoin(self.base_url, "_catalog")
        res: httpx.Response = self._client.get(url, headers=self._auth_header)
        self._raise_for_status(res)
        return self._build_response(res, Catalog)

    def get_tags(self, name: str) -> RegistryResponse:
        url: str = urljoin(self.base_url, f"{name}/tags/list")
        res: httpx.Response = self._client.get(url, headers=self._auth_header)
        self._raise_for_status(res)
        return self._build_response(res, Tags)

    def get_manifest(self, name: str, reference: str) -> RegistryResponse:
        url: str = urljoin(self.base_url, f"{name}/manifests/{reference}")
        res: httpx.Response = self._client.get(url, headers=self._auth_header)
        self._raise_for_status(res)
        return self._build_response(res, Manifest)

    def get_blob(self, name: str, digest: str) -> RegistryResponse:
        url: str = urljoin(self.base_url, f"{name}/blobs/{digest}")
        res: httpx.Response = self._client.get(url, headers=self._auth_header)
        self._raise_for_status(res)
        return self._build_response(res, Blob, from_content=True)
