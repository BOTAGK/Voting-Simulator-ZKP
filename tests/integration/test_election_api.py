"""Integration tests for the election API workflow."""

from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from app.models import Election


ElectionPayload = dict[str, Any]


def valid_election_payload(name: str = "Test election") -> ElectionPayload:
    
    now = datetime.now(timezone.utc)
    starts_at = now + timedelta(days=1)
    ends_at = starts_at + timedelta(hours=12)
    return {
        "name": name,
        "description": "Election created by an integration test.",
        "starts_at": starts_at.isoformat(),
        "ends_at": ends_at.isoformat(),
    }


def create_election(client: TestClient, name: str = "Test election") -> dict[str, Any]:
    response = client.post(
        "/api/admin/elections",
        json=valid_election_payload(name),
    )

    assert response.status_code == 201
    return response.json()


def test_create_election_persists_in_sqlite(
    admin_client: TestClient,
    test_session_factory: sessionmaker[Session],
) -> None:
    created = create_election(admin_client)

    with test_session_factory() as db:
        stored = db.get(Election, created["id"])

    assert stored is not None
    assert stored.name == "Test election"


def test_list_elections(admin_client: TestClient) -> None:
    create_election(admin_client, "First election")
    create_election(admin_client, "Second election")

    response = admin_client.get("/api/admin/elections")

    assert response.status_code == 200
    elections = response.json()
    assert len(elections) == 2
    assert {election["name"] for election in elections} == {
        "First election",
        "Second election",
    }


def test_get_single_election(admin_client: TestClient) -> None:
    created = create_election(admin_client)

    response = admin_client.get(f"/api/admin/elections/{created['id']}")

    assert response.status_code == 200
    assert response.json() == created


def test_invalid_election_dates_return_controlled_error(
    admin_client: TestClient,
) -> None:
    payload = valid_election_payload()
    starts_at = datetime.now(timezone.utc) + timedelta(days=1)
    ends_at = starts_at - timedelta(hours=12)  # Make ends_at before starts_at
    payload["starts_at"] = starts_at.isoformat()
    payload["ends_at"] = ends_at.isoformat()

    response = admin_client.post("/api/admin/elections", json=payload)

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Election end date must be after start date."
    }


def test_nonexistent_election_returns_404(admin_client: TestClient) -> None:
    response = admin_client.get("/api/admin/elections/999999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Election not found."}


def test_update_draft_election(admin_client: TestClient) -> None:
    created = create_election(admin_client)

    response = admin_client.patch(
        f"/api/admin/elections/{created['id']}",
        json={
            "name": "Updated election",
            "description": "Updated description",
        },
    )

    assert response.status_code == 200
    updated = response.json()
    assert updated["id"] == created["id"]
    assert updated["name"] == "Updated election"
    assert updated["description"] == "Updated description"
    assert updated["status"] == "draft"


def test_open_draft_election(admin_client: TestClient) -> None:
    created = create_election(admin_client)

    response = admin_client.post(f"/api/admin/elections/{created['id']}/open")

    assert response.status_code == 200
    assert response.json()["status"] == "active"


def test_close_active_election(admin_client: TestClient) -> None:
    created = create_election(admin_client)
    open_response = admin_client.post(
        f"/api/admin/elections/{created['id']}/open"
    )
    assert open_response.status_code == 200

    close_response = admin_client.post(
        f"/api/admin/elections/{created['id']}/close"
    )

    assert close_response.status_code == 200
    assert close_response.json()["status"] == "closed"


def test_cannot_update_active_election(admin_client: TestClient) -> None:
    created = create_election(admin_client)
    open_response = admin_client.post(
        f"/api/admin/elections/{created['id']}/open"
    )
    assert open_response.status_code == 200

    response = admin_client.patch(
        f"/api/admin/elections/{created['id']}",
        json={"name": "Forbidden update"},
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Only draft elections can be updated."
    }


def test_cannot_close_draft_election(admin_client: TestClient) -> None:
    created = create_election(admin_client)

    response = admin_client.post(
        f"/api/admin/elections/{created['id']}/close"
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Only active election can be closed."
    }


def test_delete_draft_election(admin_client: TestClient) -> None:
    created = create_election(admin_client)

    delete_response = admin_client.delete(
        f"/api/admin/elections/{created['id']}"
    )

    assert delete_response.status_code == 204
    assert delete_response.content == b""

    get_response = admin_client.get(f"/api/admin/elections/{created['id']}")
    assert get_response.status_code == 404
