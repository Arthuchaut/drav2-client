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
    """The registry client base class.

    Attributes:
        base_url: The base URL of the registry API (should contains the version too).
    """

    def __init__(
        self,
        base_url: str,
        user_id: Optional[str] = None,  # TODO: Define a Loggin dataclass.
        password: Optional[str] = None,  # TODO: Define a Loggin dataclass.
        transport: Optional[AnyTransport] = None,
    ) -> None:
        """The constructor.

        Args:
            base_url: The registry API base url. Should contains the version too.
            user_id (Optional): The user ID used for the registry authentication.
            password (Optional): The password used for the registry authentication.
            transport (Optional): The HTTP transport that will be used by the client.
        """

        self.base_url: str = base_url
        self._client: httpx.Client = httpx.Client(transport=transport)
        self._user_id: str | None = user_id
        self._password: str | None = password

    @cached_property
    def _auth_header(self) -> dict[str, str]:
        """Build the authorization header according to the given loggins if exists.

        Returns:
            dict[str, str]: The authorization header. Default to {} of no loggins given.
        """

        if self._user_id and self._password:
            fmt: str = f"{self._user_id}:{self._password}"
            basic: str = base64.b64encode(fmt.encode("utf8")).decode("utf8")
            return {"Authorization": f"Basic {basic}"}

        return {}

    def _build_response(
        self,
        res: httpx.Response,
        *,
        model: Optional[type[BaseModel]] = None,
        from_bytes: bool = False,
        additional_meta: dict[str, Any] = {},
    ) -> RegistryResponse[Any]:
        """Parse the registry response.

        Args:
            res: The raw HTTP response.
            model (Optional): The model to use to parse the response body.
            from_bytes (Optional): Specify the nature of the response body.
            additional_meta (Optional): Specify some additional meta to give to
                the RegistryResponse model. These meta will be given to the concerned
                models by the RegistryResponse constructor.

        Returns:
            RegistryResponse[Any]: The parsed registry response.
        """

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
    """The registry client class."""

    _DEFAULT_RESULT_SIZE: ClassVar[int] = 10

    def check_version(self) -> RegistryResponse[None | Error]:
        """Check the availability of the registry API.

        Note:
            The response status_code should be equals to 200.

        Returns:
            RegistryResponse[None | Error]: The registry response from the API.
        """

        res: httpx.Response = self._client.get(self.base_url, headers=self._auth_header)
        return self._build_response(res)

    def get_catalog(
        self, *, size: Optional[int] = _DEFAULT_RESULT_SIZE, last: Optional[str] = ""
    ) -> RegistryResponse[Catalog | Error]:
        """Retrieve the repositories list from the remote registry.

        Args:
            size (Optional): The maximum results of the given page. Default to
                _DEFAULT_RESULT_SIZE.
            last (Optional): The last item of the results that will be used to query
                the next page.

        Returns:
            RegistryResponse[Catalog | Error]: The registry response.
        """

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
    ) -> RegistryResponse[Tags | Error]:
        """Retrieve of the tags of the given repository name.

        Args:
            name: The repository name.
            size (Optional): The maximum results of the given page. Default to
                _DEFAULT_RESULT_SIZE.
            last (Optional): The last item of the results that will be used to query
                the next page.

        Returns:
            RegistryResponse[Tags | Error]: The registry response.
        """

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
    ) -> RegistryResponse[ManifestV1 | ManifestV2 | Error]:
        """Retrieve the repository's manifest.

        Args:
            name: The repository name.
            reference: The repository reference (should be a tag name).
            media_type (Optional): The expected schema version of the returned manifest.
                Default to MediaType.MANIFEST_V2.

        Returns:
            RegistryResponse[ManifestV1 | ManifestV2 | Error]: The registry response.
        """

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
        self, name: str, digest: SHA256, *, stream: bool = True
    ) -> RegistryResponse[Blob | Error]:
        """Retrieve the blob from the registry.

        Args:
            name: The repository name.
            digest: The digest of the desired blob from the manifest layers
                or the manifest digest itself.
            stream (Optional): Read the blob content in stream mode. It's strongly
                recommanded to set it to True to avoid high memory consumption.
                If the stream mode is set to True, use the
                <RegistryResponse>.body.iter_bytes() method to read the binary data.
                Default to True.

        Returns:
            RegistryResponse[Blob | Error]: The registry response.
        """

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
    ) -> RegistryResponse[None | Error]:
        """Put a manifest to the remote registry.

        Args:
            name: The repository name.
            reference: The repository reference (should be a tag name).
            manifest: The manifest to put to the registry.

        Returns:
            RegistryResponse[None | Error]: The registry response.
        """

        url: str = urljoin(self.base_url, f"{name}/manifests/{reference}")
        headers: dict[str, str] = self._auth_header
        res: httpx.Response = self._client.put(
            url, headers=headers, data=manifest.json(by_alias=True)
        )
        return self._build_response(res)

    def delete_manifest(
        self, name: str, reference: str
    ) -> RegistryResponse[None | Error]:
        """Delete a manifest from the registry.

        Args:
            name: The repository name.
            reference: The repository reference (should be a tag name).

        Returns:
            RegistryResponse[None | Error]: The registry response.
        """

        url: str = urljoin(self.base_url, f"{name}/manifests/{reference}")
        headers: dict[str, str] = self._auth_header
        res: httpx.Response = self._client.delete(url, headers=headers)
        return self._build_response(res)

    def delete_blob(self, name: str, digest: SHA256) -> RegistryResponse[None | Error]:
        """Delete a blob from the registry.

        Args:
            name: The repository name.
            digest: The digest of the desired blob from the manifest layers
                or the manifest digest itself.

        Returns:
            RegistryResponse[None | Error]: The registry response.
        """

        digest = SHA256(digest)
        digest.raise_for_validation()
        url: str = urljoin(self.base_url, f"{name}/blobs/{digest}")
        res: httpx.Response = self._client.delete(url, headers=self._auth_header)
        return self._build_response(res)

    def initiate_blob_upload(
        self, name: str, data: bytes, *, digest: Optional[SHA256] = None
    ) -> RegistryResponse[None | Error]:
        """Upload a blob to the registry.

        Args:
            name: The repository name.
            data: The binary content of the blob.
            digest (Optional): The digest that identify the uploaded blob.
                If given, given data will be used to complete the upload
                in a single request.

        Returns:
            RegistryResponse[None | Error]: The registry response.
        """

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

    def get_blob_upload(self, name: str, uuid: str) -> RegistryResponse[None | Error]:
        """Get the state of a blob upload.

        Args:
            name: The repository name.
            uuid: The identifier of the targeted blob upload.
                This information is given by the docker_upload_uuid header of the
                registry response of the initiate_blob_upload() method.

        Returns:
            RegistryResponse[None | Error]: The registry response.
        """

        url: str = urljoin(self.base_url, f"{name}/blobs/uploads/{uuid}")
        res: httpx.Response = self._client.get(url, headers=self._auth_header)
        return self._build_response(res)

    def patch_blob_upload(
        self, name: str, uuid: str, data: bytes
    ) -> RegistryResponse[None | Error]:
        """Upload a chunk of data for the specified upload.

        Args:
            name: The repository name.
            uuid: The identifier of the targeted blob upload.
                This information is given by the docker_upload_uuid header of the
                registry response of the initiate_blob_upload() method.
            data: The chunk of data to upload.

        Returns:
            RegistryResponse[None | Error]: The registry response.
        """

        url: str = urljoin(self.base_url, f"{name}/blobs/uploads/{uuid}")
        headers: dict[str, Any] = {"Content-Type": "application/octect-stream"}
        headers |= self._auth_header
        res: httpx.Response = self._client.patch(url, headers=headers, data=data)
        return self._build_response(res)

    def complete_blob_upload(
        self, name: str, uuid: str, digest: SHA256, *, data: Optional[bytes] = None
    ) -> RegistryResponse[None | Error]:
        """Complete the blob upload, optionally appending the data as the final chunk.

        Args:
            name: The repository name.
            uuid: The identifier of the targeted blob upload.
                This information is given by the docker_upload_uuid header of the
                registry response of the initiate_blob_upload() method.
            digest: The digest of the uploaded blob.
            data (Optional): The final chunk of data to upload.

        Returns:
            RegistryResponse[None | Error]: The registry response.
        """

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

    def cancel_blob_upload(
        self, name: str, uuid: str
    ) -> RegistryResponse[None | Error]:
        """Cancel a blob upload.
        The uploaded content should be removed from the registry.

        Args:
            name: The repository name.
            uuid: The identifier of the targeted blob upload.
                This information is given by the docker_upload_uuid header of the
                registry response of the initiate_blob_upload() method.

        Returns:
            RegistryResponse[None | Error]: The registry response.
        """

        url: str = urljoin(self.base_url, f"{name}/blobs/uploads/{uuid}")
        headers: dict[str, Any] = {
            "Content-Type": "application/octect-stream",
            "Content-Length": "0",
        }
        headers |= self._auth_header
        res: httpx.Response = self._client.delete(url, headers=headers)
        return self._build_response(res)
