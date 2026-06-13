"""Integration tests for the candidate API workflow."""

from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi.testclient import TestClient


def create_election(client: TestClient, name: str = "Test election") -> dict[str, Any]:
    starts_at = datetime.now(timezone.utc) + timedelta(days=1)
    ends_at = starts_at + timedelta(hours=12)

    response = client.post(
        "/api/admin/elections",
        json={
            "name": name,
            "description": "Election used by candidate tests.",
            "starts_at": starts_at.isoformat(),
            "ends_at": ends_at.isoformat(),
        },
    )

    assert response.status_code == 201
    return response.json()


def create_candidate(
    client: TestClient,
    election_id: int,
    name: str = "Test candidate",
) -> dict[str, Any]:
    response = client.post(
        f"/api/admin/elections/{election_id}/candidates",
        json={
            "name": name,
            "description": "Candidate created by an integration test.",
        },
    )

    assert response.status_code == 201
    return response.json()


def test_add_candidate_to_draft_election(admin_client: TestClient) -> None:
    election = create_election(admin_client)

    candidate = create_candidate(admin_client, election["id"])

    assert candidate["election_id"] == election["id"]
    assert candidate["name"] == "Test candidate"


def test_list_candidates_for_election(admin_client: TestClient) -> None:
    election = create_election(admin_client)
    create_candidate(admin_client, election["id"], "First candidate")
    create_candidate(admin_client, election["id"], "Second candidate")

    response = admin_client.get(
        f"/api/admin/elections/{election['id']}/candidates"
    )

    assert response.status_code == 200
    candidates = response.json()
    assert len(candidates) == 2
    assert [candidate["name"] for candidate in candidates] == [
        "First candidate",
        "Second candidate",
    ]


def test_get_candidate_for_election(admin_client: TestClient) -> None:
    election = create_election(admin_client)
    candidate = create_candidate(admin_client, election["id"])

    response = admin_client.get(
        f"/api/admin/elections/{election['id']}/candidates/{candidate['id']}"
    )

    assert response.status_code == 200
    assert response.json() == candidate


def test_update_candidate_in_draft_election(admin_client: TestClient) -> None:
    election = create_election(admin_client)
    candidate = create_candidate(admin_client, election["id"])

    response = admin_client.patch(
        f"/api/admin/elections/{election['id']}/candidates/{candidate['id']}",
        json={
            "name": "Updated candidate",
            "description": "Updated description",
        },
    )

    assert response.status_code == 200
    updated = response.json()
    assert updated["name"] == "Updated candidate"
    assert updated["description"] == "Updated description"


def test_delete_candidate_from_draft_election(admin_client: TestClient) -> None:
    election = create_election(admin_client)
    candidate = create_candidate(admin_client, election["id"])
    candidate_url = (
        f"/api/admin/elections/{election['id']}/candidates/{candidate['id']}"
    )

    delete_response = admin_client.delete(candidate_url)

    assert delete_response.status_code == 204
    assert delete_response.content == b""

    get_response = admin_client.get(candidate_url)
    assert get_response.status_code == 404
    assert get_response.json() == {"detail": "Candidate not found."}


def test_cannot_add_candidate_to_active_election(
    admin_client: TestClient,
) -> None:
    election = create_election(admin_client)
    open_response = admin_client.post(
        f"/api/admin/elections/{election['id']}/open"
    )
    assert open_response.status_code == 200

    response = admin_client.post(
        f"/api/admin/elections/{election['id']}/candidates",
        json={"name": "Forbidden candidate"},
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Candidates can only be added to draft elections."
    }


def test_nonexistent_election_returns_404_for_candidate_list(
    admin_client: TestClient,
) -> None:
    response = admin_client.get("/api/admin/elections/999999/candidates")

    assert response.status_code == 404
    assert response.json() == {"detail": "Election not found."}


def test_candidate_from_another_election_returns_404(
    admin_client: TestClient,
) -> None:
    first_election = create_election(admin_client, "First election")
    second_election = create_election(admin_client, "Second election")
    candidate = create_candidate(admin_client, first_election["id"])

    response = admin_client.get(
        f"/api/admin/elections/{second_election['id']}"
        f"/candidates/{candidate['id']}"
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Candidate not found."}
