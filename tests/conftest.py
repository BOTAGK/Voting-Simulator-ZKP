"""Shared pytest fixtures using an isolated in-memory SQLite database."""

from collections.abc import Callable, Generator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
import app.services.token_service as token_service
from app.core.config import get_settings
from app.core.database import Base
from app.core.deps import get_db
from app.main import create_app
from app.models import Election, ElectionStatus
from app.zkp.merkle import MerkleProof


class FakeMerkleTree:
    def __init__(self, leaves: list[int]) -> None:
        self.leaves = leaves
        self.root = 999_999

    def get_proof(self, leaf_index: int) -> MerkleProof:
        return MerkleProof(
            siblings=[10_000 + leaf_index, 20_000 + leaf_index],
            path_indices=[0, 1],
        )


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
def fast_token_generation(monkeypatch: pytest.MonkeyPatch) -> Generator[None, None, None]:
    monkeypatch.setattr(
        token_service,
        "generate_token_secrets",
        lambda count: list(range(101, 101 + count)),
    )
    monkeypatch.setattr(
        token_service,
        "hash_token_secrets",
        lambda token_secrets: [secret + 1_000 for secret in token_secrets],
    )
    monkeypatch.setattr(token_service, "MerkleTree", FakeMerkleTree)
    yield


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
def db_session(test_session_factory: sessionmaker[Session]) -> Generator[Session, None, None]:
    session = test_session_factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def create_db_election(
    db_session: Session,
) -> Callable[[ElectionStatus], Election]:
    def _create_election(
        status: ElectionStatus = ElectionStatus.DRAFT,
    ) -> Election:
        election = Election(
            name="Token test election",
            description="Election used by token service tests.",
            status=status,
        )
        db_session.add(election)
        db_session.commit()
        db_session.refresh(election)

        return election

    return _create_election


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
