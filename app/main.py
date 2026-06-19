"""Application entrypoint."""

from starlette.middleware.sessions import SessionMiddleware
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes.voting import router as voting_router
from app.api.routes.auth import router as auth_router
from app.api.routes.admin import router as admin_router
from app.api.routes.health import router as health_router
from app.api.routes.results import router as results_router
from app.core.config import get_settings
from app.core.database import init_db
from app.core.exception_handlers import register_exception_handlers


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    init_db()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="ZKP Voting Simulator",
        lifespan=lifespan,
    )

    settings = get_settings()

    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.session_secret_key,
        session_cookie="admin_session",
        max_age=3600,  # Session expires after 1 hour
        same_site="lax",
        #todo: set secure=True in production when using HTTPS
        https_only=False,
    )

    register_exception_handlers(app)
    app.include_router(voting_router, prefix="/api")
    app.include_router(results_router, prefix="/api")
    app.include_router(auth_router, prefix="/api")
    app.include_router(health_router, prefix="/api")
    app.include_router(admin_router, prefix="/api")

    return app


app = create_app()
