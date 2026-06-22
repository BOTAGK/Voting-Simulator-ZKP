"""Reusable helpers for API integration tests."""

from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi.testclient import TestClient


ElectionPayload = dict[str, Any]


def valid_election_payload(name: str = "Test election") -> ElectionPayload:
    now = datetime.now(timezone.utc)
    starts_at = now - timedelta(hours=1)
    ends_at = now + timedelta(days=1)

    return {
        "name": name,
        "description": "Election created by an integration test.",
        "starts_at": starts_at.isoformat(),
        "ends_at": ends_at.isoformat(),
    }


def create_election(
    client: TestClient,
    name: str = "Test election",
) -> dict[str, Any]:
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
