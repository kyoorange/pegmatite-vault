from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class ResourceNotFoundError(Exception):
    def __init__(self, resource: str, identifier: object) -> None:
        self.resource = resource
        self.identifier = identifier


class InvalidReferenceError(Exception):
    def __init__(self, resource: str, identifiers: list[object]) -> None:
        self.resource = resource
        self.identifiers = identifiers


class InvalidImageError(Exception):
    pass


class ImageTooLargeError(Exception):
    pass


class ResourceInUseError(Exception):
    def __init__(self, resource: str, identifier: object, reference_count: int) -> None:
        self.resource = resource
        self.identifier = identifier
        self.reference_count = reference_count


class DuplicateResourceError(Exception):
    def __init__(self, resource: str, field: str) -> None:
        self.resource = resource
        self.field = field


class ImportTokenError(Exception):
    pass


def error_response(status_code: int, code: str, message: str, details: Any = None) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message, "details": details}},
    )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ResourceNotFoundError)
    async def not_found_handler(_: Request, exc: ResourceNotFoundError) -> JSONResponse:
        return error_response(
            404,
            "resource_not_found",
            "対象のデータが見つかりません。",
            {"resource": exc.resource, "id": str(exc.identifier)},
        )

    @app.exception_handler(InvalidReferenceError)
    async def invalid_reference_handler(_: Request, exc: InvalidReferenceError) -> JSONResponse:
        return error_response(
            422,
            "invalid_reference",
            "関連データが見つかりません。",
            {"resource": exc.resource, "ids": [str(value) for value in exc.identifiers]},
        )

    @app.exception_handler(InvalidImageError)
    async def invalid_image_handler(_: Request, exc: InvalidImageError) -> JSONResponse:
        return error_response(415, "unsupported_image", str(exc))

    @app.exception_handler(ImageTooLargeError)
    async def image_too_large_handler(_: Request, __: ImageTooLargeError) -> JSONResponse:
        return error_response(413, "image_too_large", "画像サイズが上限を超えています。")

    @app.exception_handler(ResourceInUseError)
    async def resource_in_use_handler(_: Request, exc: ResourceInUseError) -> JSONResponse:
        return error_response(
            409,
            "resource_in_use",
            "標本から使用されているため削除できません。",
            {
                "resource": exc.resource,
                "id": str(exc.identifier),
                "reference_count": exc.reference_count,
            },
        )

    @app.exception_handler(DuplicateResourceError)
    async def duplicate_resource_handler(_: Request, exc: DuplicateResourceError) -> JSONResponse:
        return error_response(
            409,
            "duplicate_resource",
            "同じ名前のデータがすでに登録されています。",
            {"resource": exc.resource, "field": exc.field},
        )

    @app.exception_handler(ImportTokenError)
    async def import_token_handler(_: Request, exc: ImportTokenError) -> JSONResponse:
        return error_response(409, "invalid_import_token", str(exc))

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        return error_response(
            422,
            "validation_error",
            "入力値が不正です。",
            exc.errors(),
        )
