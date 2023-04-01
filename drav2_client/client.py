import base64
from functools import cached_property
from typing import Optional
from urllib.parse import urljoin
import httpx
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
        self._client: httpx.Client = httpx.Client(transport=transport)
        self.base_url: str = base_url
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

    def get_tags_list(self, name: str) -> TagsList:
        url: str = urljoin(self.base_url, f"{name}/tags/list")
        res: httpx.Response = self._client.get(url, headers=self._auth_header)
        self._raise_for_status(res)
        return TagsList.parse_obj(res.json())

    def get_manifest(self, name: str, reference: str) -> Manifest:
        url: str = urljoin(self.base_url, f"{name}/manifests/{reference}")
        res: httpx.Response = self._client.get(url, headers=self._auth_header)
        self._raise_for_status(res)
        return Manifest.parse_obj(res.json())
