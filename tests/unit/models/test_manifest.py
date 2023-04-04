from typing import Any, Callable
from pydantic import ValidationError
import pytest
from pytest_mock import MockerFixture

from drav2_client.models.manifest import (
    Config,
    FsLayer,
    Signature,
    Header,
    HistoryItem,
    Jwk,
    Layer,
    ManifestV1,
    ManifestV2,
)


class TestManifestV2:
    @pytest.mark.parametrize(
        "data, expected, throwable",
        [
            (
                {
                    "schemaVersion": 2,
                    "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
                    "config": {
                        "mediaType": "application/vnd.docker.image.v1+json",
                        "size": 12345,
                        "digest": "sha256:dh3n8lkf65dd078d",
                    },
                    "layers": [
                        {
                            "mediaType": "application/vnd.docker.image.v1+json",
                            "size": 12345,
                            "digest": "sha256:d8kd04di3n12u10",
                        },
                    ],
                },
                ManifestV2.construct(
                    schema_version=2,
                    media_type="application/vnd.docker.distribution.manifest.v2+json",
                    config=Config.construct(
                        media_type="application/vnd.docker.image.v1+json",
                        size=12345,
                        digest="sha256:dh3n8lkf65dd078d",
                    ),
                    layers=[
                        Layer.construct(
                            media_type="application/vnd.docker.image.v1+json",
                            size=12345,
                            digest="sha256:d8kd04di3n12u10",
                        )
                    ],
                ),
                None,
            ),
            (
                {},
                ManifestV2.construct(
                    schema_version=None,
                    media_type=None,
                    config=None,
                    layers=[],
                ),
                None,
            ),
            (
                {
                    "schemaVersion": None,
                    "mediaType": None,
                    "config": {
                        "mediaType": None,
                        "size": None,
                        "digest": None,
                    },
                    "layers": [
                        {
                            "mediaType": None,
                            "size": None,
                            "digest": None,
                        },
                    ],
                },
                ManifestV2.construct(
                    schema_version=None,
                    media_type=None,
                    config=Config.construct(
                        media_type="",
                        size=None,
                        digest="",
                    ),
                    layers=[
                        Layer.construct(
                            media_type="",
                            size=None,
                            digest="",
                        )
                    ],
                ),
                None,
            ),
            (
                {
                    "schemaVersion": None,
                    "mediaType": None,
                    "config": {},
                    "layers": [
                        {},
                    ],
                },
                ManifestV2.construct(
                    schema_version=None,
                    media_type=None,
                    config=Config.construct(
                        media_type="",
                        size=None,
                        digest="",
                    ),
                    layers=[
                        Layer.construct(
                            media_type="",
                            size=None,
                            digest="",
                        )
                    ],
                ),
                None,
            ),
            (
                {
                    "schemaVersion": None,
                    "mediaType": None,
                    "config": None,
                    "layers": None,
                },
                ManifestV2.construct(
                    schema_version=None,
                    media_type=None,
                    config=None,
                    layers=[],
                ),
                None,
            ),
            (
                {
                    "schemaVersion": "hello",
                    "mediaType": [],
                    "config": {
                        "mediaType": {},
                        "size": "hello",
                        "digest": [],
                    },
                    "layers": [
                        {
                            "mediaType": {},
                            "size": "hello",
                            "digest": [],
                        },
                    ],
                },
                (
                    ".schemaVersion",
                    ".mediaType",
                    ".config.mediaType",
                    ".config.size",
                    ".config.digest",
                    ".layers[0].mediaType",
                    ".layers[0].size",
                    ".layers[0].digest",
                ),
                ValidationError,
            ),
            (
                {
                    "schemaVersion": "hello",
                    "mediaType": [],
                    "config": [],
                    "layers": [None],
                },
                (
                    ".schemaVersion",
                    ".mediaType",
                    # ".config", # Skip it due to a strange behaviour of Pydantic (not throwing ValidationError)
                    ".layers[0]",
                ),
                ValidationError,
            ),
            (
                {
                    "schemaVersion": "hello",
                    "mediaType": [],
                    "config": [],
                    "layers": "hello",
                },
                (
                    ".schemaVersion",
                    ".mediaType",
                    # ".config", # Skip it due to a strange behaviour of Pydantic (not throwing ValidationError)
                    ".layers",
                ),
                ValidationError,
            ),
        ],
    )
    def test_init(
        self,
        data: dict[str, Any],
        expected: ManifestV2 | tuple[str, ...],
        throwable: type[ValidationError] | None,
        extract_error_list: Callable[[Any], Any],
        assert_sequences_equals: Callable[[Any], Any],
    ) -> None:
        if throwable:
            try:
                ManifestV2.parse_obj(data)
                raise AssertionError(f"Did not raise {throwable}")  # pragma: no cover
            except throwable as e:
                error_list: list[str] = extract_error_list(e)
                assert_sequences_equals(error_list, expected)
        else:
            assert ManifestV2.parse_obj(data) == expected

    def test_total_size_property(self, mocker: MockerFixture) -> None:
        manifest: ManifestV2 = ManifestV2(
            layers=[
                Layer(size=2),
                Layer(size=4),
                Layer(size=6),
                Layer(size=8),
            ]
        )
        assert manifest.total_size == 20
        manifest.layers = [
            Layer(size=2),
            Layer(size=4),
        ]
        assert manifest.total_size == 20


class TestManifestV1:
    @pytest.mark.parametrize(
        "data, expected, throwable",
        [
            (
                {
                    "schemaVersion": 1,
                    "name": "python",
                    "tag": "latest",
                    "architecture": "arm64",
                    "fsLayers": [
                        {
                            "blobSum": "sha256:a3ed95caeb02ffe68cdd9f",
                        },
                    ],
                    "history": [
                        {
                            "v1Compatibility": "abc",
                        },
                    ],
                    "signatures": [
                        {
                            "header": {
                                "jwk": {
                                    "crv": "P-256",
                                    "kid": "PZQP:BG5K:OCSU:QBDE:WYJT:NTRL",
                                    "kty": "EC",
                                    "x": "eVQw1KUQzqbl3TLQZfPpA0sE",
                                    "y": "uKbkv4DknWbByW9CyT8pJMD",
                                },
                                "alg": "ES256",
                            },
                            "signature": "qfOubO7xHLpbkFYFF19mXpgtbeRT",
                            "protected": "eyJmb3JtYXRMZW5ndGgiOjIwODAs",
                        }
                    ],
                },
                ManifestV1.construct(
                    schema_version=1,
                    name="python",
                    tag="latest",
                    architecture="arm64",
                    fs_layers=[
                        FsLayer.construct(
                            blob_sum="sha256:a3ed95caeb02ffe68cdd9f",
                        )
                    ],
                    history=[
                        HistoryItem.construct(
                            v1_compatibility="abc",
                        ),
                    ],
                    signatures=[
                        Signature.construct(
                            header=Header.construct(
                                jwk=Jwk.construct(
                                    crv="P-256",
                                    kid="PZQP:BG5K:OCSU:QBDE:WYJT:NTRL",
                                    kty="EC",
                                    x="eVQw1KUQzqbl3TLQZfPpA0sE",
                                    y="uKbkv4DknWbByW9CyT8pJMD",
                                ),
                                alg="ES256",
                            ),
                            signature="qfOubO7xHLpbkFYFF19mXpgtbeRT",
                            protected="eyJmb3JtYXRMZW5ndGgiOjIwODAs",
                        ),
                    ],
                ),
                None,
            ),
            (
                {},
                ManifestV1.construct(
                    schema_version=None,
                    name="",
                    tag="",
                    architecture="",
                    fs_layers=[],
                    history=[],
                    signatures=[],
                ),
                None,
            ),
            (
                {
                    "schemaVersion": None,
                    "name": None,
                    "tag": None,
                    "architecture": None,
                    "fsLayers": None,
                    "history": None,
                    "signatures": None,
                },
                ManifestV1.construct(
                    schema_version=None,
                    name="",
                    tag="",
                    architecture="",
                    fs_layers=[],
                    history=[],
                    signatures=[],
                ),
                None,
            ),
            (
                {
                    "schemaVersion": None,
                    "name": None,
                    "tag": None,
                    "architecture": None,
                    "fsLayers": [
                        {},
                    ],
                    "history": [
                        {},
                    ],
                    "signatures": [{}],
                },
                ManifestV1.construct(
                    schema_version=None,
                    name="",
                    tag="",
                    architecture="",
                    fs_layers=[
                        FsLayer.construct(
                            blob_sum="",
                        )
                    ],
                    history=[
                        HistoryItem.construct(
                            v1_compatibility="",
                        ),
                    ],
                    signatures=[
                        Signature.construct(
                            header=None,
                            signature="",
                            protected="",
                        ),
                    ],
                ),
                None,
            ),
            (
                {
                    "schemaVersion": None,
                    "name": None,
                    "tag": None,
                    "architecture": None,
                    "fsLayers": [
                        {
                            "blobSum": None,
                        },
                    ],
                    "history": [
                        {
                            "v1Compatibility": None,
                        },
                    ],
                    "signatures": [
                        {
                            "header": {
                                "jwk": {},
                                "alg": None,
                            },
                            "signature": None,
                            "protected": None,
                        }
                    ],
                },
                ManifestV1.construct(
                    schema_version=None,
                    name="",
                    tag="",
                    architecture="",
                    fs_layers=[
                        FsLayer.construct(
                            blob_sum="",
                        )
                    ],
                    history=[
                        HistoryItem.construct(
                            v1_compatibility="",
                        ),
                    ],
                    signatures=[
                        Signature.construct(
                            header=Header.construct(
                                jwk=Jwk.construct(
                                    crv="",
                                    kid="",
                                    kty="",
                                    x="",
                                    y="",
                                ),
                                alg="",
                            ),
                            signature="",
                            protected="",
                        ),
                    ],
                ),
                None,
            ),
            (
                {
                    "schemaVersion": None,
                    "name": None,
                    "tag": None,
                    "architecture": None,
                    "fsLayers": [
                        {
                            "blobSum": None,
                        },
                    ],
                    "history": [
                        {
                            "v1Compatibility": None,
                        },
                    ],
                    "signatures": [
                        {
                            "header": {
                                "jwk": {
                                    "crv": None,
                                    "kid": None,
                                    "kty": None,
                                    "x": None,
                                    "y": None,
                                },
                                "alg": None,
                            },
                            "signature": None,
                            "protected": None,
                        }
                    ],
                },
                ManifestV1.construct(
                    schema_version=None,
                    name="",
                    tag="",
                    architecture="",
                    fs_layers=[
                        FsLayer.construct(
                            blob_sum="",
                        )
                    ],
                    history=[
                        HistoryItem.construct(
                            v1_compatibility="",
                        ),
                    ],
                    signatures=[
                        Signature.construct(
                            header=Header.construct(
                                jwk=Jwk.construct(
                                    crv="",
                                    kid="",
                                    kty="",
                                    x="",
                                    y="",
                                ),
                                alg="",
                            ),
                            signature="",
                            protected="",
                        ),
                    ],
                ),
                None,
            ),
            (
                {
                    "schemaVersion": "abc",
                    "name": [],
                    "tag": {},
                    "architecture": [],
                    "fsLayers": "abc",
                    "history": {},
                    "signatures": 12345,
                },
                (
                    ".schemaVersion",
                    ".name",
                    ".tag",
                    ".architecture",
                    ".fsLayers",
                    ".history",
                    ".signatures",
                ),
                ValidationError,
            ),
            (
                {
                    "schemaVersion": "abc",
                    "name": [],
                    "tag": {},
                    "architecture": [],
                    "fsLayers": [
                        "abc",
                        1234,
                        None,
                        {
                            "blobSum": [],
                        },
                    ],
                    "history": [
                        "abc",
                        1234,
                        None,
                        {
                            "v1Compatibility": [],
                        },
                    ],
                    "signatures": [
                        "abc",
                        1234,
                        None,
                        {
                            "header": {
                                "jwk": {
                                    "crv": [],
                                    "kid": [],
                                    "kty": [],
                                    "x": [],
                                    "y": [],
                                },
                                "alg": [],
                            },
                            "signature": [],
                            "protected": [],
                        },
                    ],
                },
                (
                    ".schemaVersion",
                    ".name",
                    ".tag",
                    ".architecture",
                    ".fsLayers[0]",
                    ".fsLayers[1]",
                    ".fsLayers[2]",
                    ".fsLayers[3].blobSum",
                    ".history[0]",
                    ".history[1]",
                    ".history[2]",
                    ".history[3].v1Compatibility",
                    ".signatures[0]",
                    ".signatures[1]",
                    ".signatures[2]",
                    ".signatures[3].header.jwk.crv",
                    ".signatures[3].header.jwk.kid",
                    ".signatures[3].header.jwk.kty",
                    ".signatures[3].header.jwk.x",
                    ".signatures[3].header.jwk.y",
                    ".signatures[3].header.alg",
                    ".signatures[3].signature",
                    ".signatures[3].protected",
                ),
                ValidationError,
            ),
        ],
    )
    def test_init(
        self,
        data: dict[str, Any],
        expected: ManifestV1 | tuple[str, ...],
        throwable: type[ValidationError] | None,
        extract_error_list: Callable[[Any], Any],
        assert_sequences_equals: Callable[[Any], Any],
    ) -> None:
        if throwable:
            try:
                ManifestV1.parse_obj(data)
                raise AssertionError(f"Did not raise {throwable}")  # pragma: no cover
            except throwable as e:
                error_list: list[str] = extract_error_list(e)
                assert_sequences_equals(error_list, expected)
        else:
            assert ManifestV1.parse_obj(data) == expected
