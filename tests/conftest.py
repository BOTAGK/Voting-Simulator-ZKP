"""Shared pytest fixtures using an isolated in-memory SQLite database."""

from collections.abc import Generator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings
import app.models  # noqa: F401
from app.core.database import Base
from app.core.deps import get_db
from app.main import create_app

@pytest.fixture
def admin_client(client: TestClient) -> TestClient:
    settings = get_settings()
    
    response = client.post(
        "/api/auth/login",
        json={
            "username": settings.admin_username,
            "password": settings.admin_password,
        },
    )

    assert response.status_code == 200
    return client

@pytest.fixture
def test_session_factory() -> Generator[sessionmaker[Session], None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    session_factory = sessionmaker(
        bind=engine,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
    )

    Base.metadata.create_all(bind=engine)
    yield session_factory
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def test_app(test_session_factory: sessionmaker[Session]) -> FastAPI:
    app = create_app()

    def override_get_db() -> Generator[Session, None, None]:
        db = test_session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    return app


@pytest.fixture
def client(test_app: FastAPI) -> Generator[TestClient, None, None]:
    client = TestClient(test_app)
    yield client
    client.close()
