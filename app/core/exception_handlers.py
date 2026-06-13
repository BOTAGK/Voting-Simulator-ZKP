"""HTTP handlers for domain-level application exceptions."""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.core.exceptions import NotFoundError, ValidationError


async def not_found_error_handler(
    _request: Request,
    exc: NotFoundError,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": str(exc)},
    )


async def validation_error_handler(
    _request: Request,
    exc: ValidationError,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)},
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(NotFoundError, not_found_error_handler)
    app.add_exception_handler(ValidationError, validation_error_handler)

