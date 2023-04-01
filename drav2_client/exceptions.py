__all__: list[str] = [
    "HTTPError",
    "BadRequest",
    "Unauthorized",
    "NotFound",
    "InternalServerError",
    "UnknownHTTPError",
]


class HTTPError(Exception):
    ...


class BadRequest(HTTPError):
    ...


class Unauthorized(HTTPError):
    ...


class NotFound(HTTPError):
    ...


class InternalServerError(HTTPError):
    ...


class UnknownHTTPError(HTTPError):
    ...
