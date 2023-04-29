import base64
from functools import cached_property
import json
from typing import Any, ClassVar, Iterable, Iterator, Literal, Optional
from urllib.parse import urljoin
import httpx
from pydantic import BaseModel
from drav2_client.types import SHA256, AnyTransport, MediaType
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

    @classmethod
    def _bytes_iterator(cls, res: httpx.Response) -> Iterator[bytes]:
        def wrapper(chunk_size: int = 1024) -> Iterator[bytes]:
            try:
                yield from res.iter_bytes(chunk_size=chunk_size)
            finally:
                res.close()

        return wrapper

    def _build_response(
        self,
        res: httpx.Response,
        *,
        model: Optional[type[BaseModel]] = None,
        from_stream: bool = False,
        from_content: bool = False,
    ) -> RegistryResponse:
        result: BaseModel | None = None

        if res.status_code >= 500:
            result = Errors(errors=[Error(code=Error.Code.INTERNAL_ERROR)])
        elif res.status_code >= 400:
            obj: dict[str, Any]

            if from_stream:  # Because sparse is better than dense...
                obj = json.loads(*res.iter_bytes())
            else:
                obj = res.json()

            result = Errors.parse_obj(obj)
        elif model:
            if from_stream:
                result = model.parse_obj(dict(iter_bytes=self._bytes_iterator(res)))
            elif from_content:
                result = model.parse_obj(dict(content=res.content))
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
        return self._build_response(res, model=Catalog)

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
        return self._build_response(res, model=Tags)

    def get_manifest(
        self,
        name: str,
        reference: str,
        *,
        media_type: Literal[
            MediaType.MANIFEST_V2,
            MediaType.SIGNED_MANIFEST_V1,
            MediaType.MANIFEST_V1,
        ] = MediaType.MANIFEST_V2,
    ) -> RegistryResponse:
        url: str = urljoin(self.base_url, f"{name}/manifests/{reference}")
        headers: dict[str, str] = self._auth_header
        headers |= {"Accept": media_type}
        res: httpx.Response = self._client.get(url, headers=headers)
        model: type[BaseModel] = ManifestV2

        if media_type is MediaType.SIGNED_MANIFEST_V1:
            model = ManifestV1

        return self._build_response(res, model=model)

    def get_blob(
        self, name: str, digest: SHA256, *, stream: bool = False
    ) -> RegistryResponse:
        digest = SHA256(digest)
        digest.raise_for_validation()
        url: str = urljoin(self.base_url, f"{name}/blobs/{digest}")
        req: httpx.Request = self._client.build_request(
            "GET", url, headers=self._auth_header
        )
        res: httpx.Response = self._client.send(req, stream=stream)
        return self._build_response(
            res, model=Blob, from_stream=stream, from_content=not stream
        )

    def delete_manifest(self, name: str, reference: str) -> RegistryResponse:
        url: str = urljoin(self.base_url, f"{name}/manifests/{reference}")
        headers: dict[str, str] = self._auth_header
        res: httpx.Response = self._client.delete(url, headers=headers)
        return self._build_response(res)

    def delete_blob(self, name: str, digest: SHA256) -> RegistryResponse:
        digest = SHA256(digest)
        digest.raise_for_validation()
        url: str = urljoin(self.base_url, f"{name}/blobs/{digest}")
        res: httpx.Response = self._client.delete(url, headers=self._auth_header)
        return self._build_response(res)
