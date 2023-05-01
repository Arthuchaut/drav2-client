import base64
from functools import cached_property
import json
from typing import Any, ClassVar, Iterator, Literal, Optional
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
        from_bytes: bool = False,
        additional_meta: dict[str, Any] = {},
    ) -> RegistryResponse:
        result: BaseModel | None = None
        additional_meta["client"] = self

        if res.status_code >= 500:
            result = Errors(errors=[Error(code=Error.Code.INTERNAL_ERROR)])
        elif res.status_code >= 400:
            result = Errors.parse_obj(json.loads(*res.iter_bytes()))
        elif model:
            if from_bytes:
                result = model(res=res)
            else:
                result = model.parse_obj(res.json())

        return RegistryResponse(
            status_code=res.status_code,
            headers=Headers.parse_obj(res.headers),
            body=result,
            additional_meta=additional_meta,
        )


class RegistryClient(_BaseClient):
    _DEFAULT_RESULT_SIZE: ClassVar[int] = 10

    def check_version(self) -> RegistryResponse:
        res: httpx.Response = self._client.get(self.base_url, headers=self._auth_header)
        return self._build_response(res)

    def get_catalog(
        self, *, size: Optional[int] = _DEFAULT_RESULT_SIZE, last: Optional[str] = ""
    ) -> RegistryResponse[Catalog]:
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
    ) -> RegistryResponse[Tags]:
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
    ) -> RegistryResponse[ManifestV1 | ManifestV2]:
        url: str = urljoin(self.base_url, f"{name}/manifests/{reference}")
        headers: dict[str, str] = self._auth_header
        headers |= {"Accept": media_type}
        res: httpx.Response = self._client.get(url, headers=headers)
        model: type[BaseModel] = ManifestV1
        additional_meta: dict[str, Any] = {}

        if media_type is MediaType.MANIFEST_V2:
            model = ManifestV2
            additional_meta["name"] = name

        return self._build_response(res, model=model, additional_meta=additional_meta)

    def get_blob(
        self, name: str, digest: SHA256, *, stream: bool = False
    ) -> RegistryResponse[Blob]:
        digest = SHA256(digest)
        digest.raise_for_validation()
        url: str = urljoin(self.base_url, f"{name}/blobs/{digest}")
        req: httpx.Request = self._client.build_request(
            "GET", url, headers=self._auth_header
        )
        res: httpx.Response = self._client.send(req, stream=stream)
        return self._build_response(res, model=Blob, from_bytes=True)

    def put_manifest(
        self, name: str, reference: str, manifest: ManifestV1 | ManifestV2
    ) -> RegistryResponse:
        url: str = urljoin(self.base_url, f"{name}/manifests/{reference}")
        headers: dict[str, str] = self._auth_header
        res: httpx.Response = self._client.put(
            url, headers=headers, data=manifest.json(by_alias=True)
        )
        return self._build_response(res)

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

    def upload_blob(
        self, name: str, data: bytes, *, digest: Optional[SHA256] = None
    ) -> RegistryResponse:
        params: dict[str, str] = {}

        if digest is not None:
            digest = SHA256(digest)
            digest.raise_for_validation()
            params["digest"] = digest

        url: str = urljoin(self.base_url, f"{name}/blobs/uploads/")
        headers: dict[str, Any] = {
            "Content-Length": str(len(data)),
            "Content-Type": "application/octect-stream",
        }
        headers |= self._auth_header
        res: httpx.Response = self._client.post(
            url, headers=headers, params=params, data=data
        )
        return self._build_response(res)

    def get_blob_upload(self, name: str, uuid: str) -> RegistryResponse:
        url: str = urljoin(self.base_url, f"{name}/blobs/uploads/{uuid}")
        res: httpx.Response = self._client.get(url, headers=self._auth_header)
        return self._build_response(res)

    def patch_blob_upload(self, name: str, uuid: str, data: bytes) -> RegistryResponse:
        url: str = urljoin(self.base_url, f"{name}/blobs/uploads/{uuid}")
        headers: dict[str, Any] = {"Content-Type": "application/octect-stream"}
        headers |= self._auth_header
        res: httpx.Response = self._client.patch(url, headers=headers, data=data)
        return self._build_response(res)

    def put_blob_upload(
        self, name: str, uuid: str, digest: SHA256, *, data: Optional[bytes] = None
    ) -> RegistryResponse:
        url: str = urljoin(self.base_url, f"{name}/blobs/uploads/{uuid}")
        digest = SHA256(digest)
        digest.raise_for_validation()
        params: dict[str, str] = {"digest": digest}
        headers: dict[str, Any] = {
            "Content-Type": "application/octect-stream",
            "Content-length": "0",
        }

        if data is not None:
            headers["Content-Length"] = str(len(data))

        headers |= self._auth_header
        res: httpx.Response = self._client.put(
            url, headers=headers, params=params, data=data
        )
        return self._build_response(res)

    def delete_blob_upload(self, name: str, uuid: str) -> RegistryResponse:
        url: str = urljoin(self.base_url, f"{name}/blobs/uploads/{uuid}")
        headers: dict[str, Any] = {
            "Content-Type": "application/octect-stream",
            "Content-Length": "0",
        }
        headers |= self._auth_header
        res: httpx.Response = self._client.delete(url, headers=headers)
        return self._build_response(res)
