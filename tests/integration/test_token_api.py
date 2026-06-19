"""Integration tests for administrator voter token API."""

import json
from datetime import datetime, timedelta, timezone
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from app.models import Election, VoterToken


pytestmark = pytest.mark.usefixtures("fast_token_generation")


def valid_election_payload(name: str = "Token API election") -> dict[str, Any]:
    starts_at = datetime.now(timezone.utc) + timedelta(days=1)
    ends_at = starts_at + timedelta(hours=12)

    return {
        "name": name,
        "description": "Election used by token API tests.",
        "starts_at": starts_at.isoformat(),
        "ends_at": ends_at.isoformat(),
    }


def create_election(client: TestClient, name: str = "Token API election") -> dict[str, Any]:
    response = client.post(
        "/api/admin/elections",
        json=valid_election_payload(name),
    )

    assert response.status_code == 201
    return response.json()


def generate_tokens(
    client: TestClient,
    election_id: int,
    count: int = 2,
    label_prefix: str | None = "voter",
) -> list[dict[str, Any]]:
    response = client.post(
        f"/api/admin/elections/{election_id}/tokens/generate",
        json={
            "count": count,
            "label_prefix": label_prefix,
        },
    )

    assert response.status_code == 201
    return response.json()


def test_admin_can_generate_voter_tokens(admin_client: TestClient) -> None:
    election = create_election(admin_client)

    packages = generate_tokens(admin_client, election["id"])

    assert len(packages) == 2
    assert packages[0] == {
        "election_id": election["id"],
        "token_secret": "101",
        "merkle_root": "999999",
        "merkle_index": 0,
        "merkle_proof": {
            "siblings": ["10000", "20000"],
            "path_indices": [0, 1],
        },
    }
    assert packages[1]["token_secret"] == "102"
    assert packages[1]["merkle_index"] == 1


def test_generate_voter_tokens_requires_admin_session(client: TestClient) -> None:
    response = client.post(
        "/api/admin/elections/1/tokens/generate",
        json={
            "count": 1,
            "label_prefix": "voter",
        },
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Admin authentication required."}


def test_generate_voter_tokens_persists_tokens_and_merkle_root(
    admin_client: TestClient,
    test_session_factory: sessionmaker[Session],
) -> None:
    election = create_election(admin_client)

    generate_tokens(admin_client, election["id"])

    with test_session_factory() as db:
        stored_election = db.get(Election, election["id"])
        stored_tokens = (
            db.query(VoterToken)
            .filter(VoterToken.election_id == election["id"])
            .order_by(VoterToken.merkle_index.asc())
            .all()
        )

    assert stored_election is not None
    assert stored_election.merkle_root == "999999"
    assert len(stored_tokens) == 2
    assert [token.token_hash for token in stored_tokens] == ["1101", "1102"]
    assert [token.merkle_index for token in stored_tokens] == [0, 1]
    assert [token.label_for_admin for token in stored_tokens] == [
        "voter-1",
        "voter-2",
    ]
    assert all(token.merkle_path_json is not None for token in stored_tokens)
    assert json.loads(stored_tokens[0].merkle_path_json or "{}") == {
        "siblings": ["10000", "20000"],
        "path_indices": [0, 1],
    }


def test_generate_voter_tokens_rejects_second_generation(
    admin_client: TestClient,
) -> None:
    election = create_election(admin_client)
    generate_tokens(admin_client, election["id"], count=1)

    response = admin_client.post(
        f"/api/admin/elections/{election['id']}/tokens/generate",
        json={
            "count": 1,
            "label_prefix": "again",
        },
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Voter tokens have already been generated for this election."
    }


def test_generate_voter_tokens_rejects_active_election(
    admin_client: TestClient,
) -> None:
    election = create_election(admin_client)
    open_response = admin_client.post(f"/api/admin/elections/{election['id']}/open")
    assert open_response.status_code == 200

    response = admin_client.post(
        f"/api/admin/elections/{election['id']}/tokens/generate",
        json={
            "count": 1,
            "label_prefix": "voter",
        },
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Voter tokens can only be generated for draft elections."
    }


def test_generate_voter_tokens_returns_404_for_missing_election(
    admin_client: TestClient,
) -> None:
    response = admin_client.post(
        "/api/admin/elections/999999/tokens/generate",
        json={
            "count": 1,
            "label_prefix": "voter",
        },
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Election not found."}


def test_list_voter_tokens_returns_generated_tokens_without_secrets(
    admin_client: TestClient,
) -> None:
    election = create_election(admin_client)
    generate_tokens(admin_client, election["id"])

    response = admin_client.get(f"/api/admin/elections/{election['id']}/tokens")

    assert response.status_code == 200
    tokens = response.json()
    assert len(tokens) == 2
    assert tokens[0]["election_id"] == election["id"]
    assert tokens[0]["token_hash"] == "1101"
    assert tokens[0]["merkle_index"] == 0
    assert tokens[0]["label_for_admin"] == "voter-1"
    assert "token_secret" not in tokens[0]
    assert tokens[0]["merkle_path_json"] is not None
    assert json.loads(tokens[0]["merkle_path_json"]) == {
        "siblings": ["10000", "20000"],
        "path_indices": [0, 1],
    }


def test_list_voter_tokens_returns_empty_list_before_generation(
    admin_client: TestClient,
) -> None:
    election = create_election(admin_client)

    response = admin_client.get(f"/api/admin/elections/{election['id']}/tokens")

    assert response.status_code == 200
    assert response.json() == []


def test_list_voter_tokens_requires_admin_session(client: TestClient) -> None:
    response = client.get("/api/admin/elections/1/tokens")

    assert response.status_code == 401
    assert response.json() == {"detail": "Admin authentication required."}


def test_list_voter_tokens_returns_404_for_missing_election(
    admin_client: TestClient,
) -> None:
    response = admin_client.get("/api/admin/elections/999999/tokens")

    assert response.status_code == 404
    assert response.json() == {"detail": "Election not found."}
