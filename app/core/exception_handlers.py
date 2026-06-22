"""HTTP handlers for domain-level application exceptions."""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.core.exceptions import (
    ConflictError,
    NotFoundError,
    ServiceUnavailableError,
    ValidationError,
)


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


async def conflict_error_handler(
    _request: Request,
    exc: ConflictError,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": str(exc)},
    )


async def service_unavailable_error_handler(
    _request: Request,
    exc: ServiceUnavailableError,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"detail": str(exc)},
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(NotFoundError, not_found_error_handler)
    app.add_exception_handler(ValidationError, validation_error_handler)
    app.add_exception_handler(ConflictError, conflict_error_handler)
    app.add_exception_handler(
        ServiceUnavailableError,
        service_unavailable_error_handler,
    )
