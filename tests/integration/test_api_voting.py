from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
import pytest
from sqlalchemy.orm import Session

from app.models import Candidate, Election, ElectionStatus
from app.services import voting_service


def create_election(
    db_session: Session,
    status: ElectionStatus,
    name: str = "Public election",
    starts_at=None,
    ends_at=None,
) -> Election:
    now = datetime.now(timezone.utc)
    election = Election(
        name=name,
        description=f"{name} description",
        status=status,
        merkle_root="test-merkle-root",
        starts_at=starts_at if starts_at is not None else now - timedelta(hours=1),
        ends_at=ends_at if ends_at is not None else now + timedelta(days=1),
    )
    db_session.add(election)
    db_session.commit()
    db_session.refresh(election)

    return election


def create_candidate(
    db_session: Session,
    election_id: int,
    name: str = "Candidate",
) -> Candidate:
    candidate = Candidate(
        election_id=election_id,
        name=name,
        description=f"{name} description",
    )
    db_session.add(candidate)
    db_session.commit()
    db_session.refresh(candidate)

    return candidate


def build_vote_payload(
    candidate_id: int,
    election_id: int,
    merkle_root: str,
    nullifier_hash: str = "nullifier-1",
) -> dict:
    return {
        "candidate_id": candidate_id,
        "nullifier_hash": nullifier_hash,
        "proof": {"proof": "demo"},
        "public_signals": {
            "election_id": election_id,
            "merkle_root": merkle_root,
            "nullifier_hash": nullifier_hash,
        },
    }


def test_list_active_elections_returns_active_election(
    client: TestClient,
    db_session: Session,
) -> None:
    active_election = create_election(
        db_session,
        ElectionStatus.ACTIVE,
        name="Active election",
    )

    response = client.get("/api/elections/active")

    assert response.status_code == 200
    election_ids = [election["id"] for election in response.json()]
    assert active_election.id in election_ids


def test_list_active_elections_does_not_return_draft_election(
    client: TestClient,
    db_session: Session,
) -> None:
    active_election = create_election(
        db_session,
        ElectionStatus.ACTIVE,
        name="Visible active election",
    )
    draft_election = create_election(
        db_session,
        ElectionStatus.DRAFT,
        name="Hidden draft election",
    )

    response = client.get("/api/elections/active")

    assert response.status_code == 200
    election_ids = [election["id"] for election in response.json()]
    assert active_election.id in election_ids
    assert draft_election.id not in election_ids


def test_list_active_elections_does_not_return_future_active_election(
    client: TestClient,
    db_session: Session,
) -> None:
    now = datetime.now(timezone.utc)
    active_election = create_election(
        db_session,
        ElectionStatus.ACTIVE,
        name="Currently active election",
    )
    future_election = create_election(
        db_session,
        ElectionStatus.ACTIVE,
        name="Future active election",
        starts_at=now + timedelta(days=1),
        ends_at=now + timedelta(days=2),
    )

    response = client.get("/api/elections/active")

    assert response.status_code == 200
    election_ids = [election["id"] for election in response.json()]
    assert active_election.id in election_ids
    assert future_election.id not in election_ids


def test_get_election_by_id_returns_active_election(
    client: TestClient,
    db_session: Session,
) -> None:
    active_election = create_election(
        db_session,
        ElectionStatus.ACTIVE,
        name="Active details election",
    )

    response = client.get(f"/api/elections/{active_election.id}")

    assert response.status_code == 200
    assert response.json()["id"] == active_election.id
    assert response.json()["status"] == ElectionStatus.ACTIVE.value


def test_get_election_by_draft_id_returns_404(
    client: TestClient,
    db_session: Session,
) -> None:
    draft_election = create_election(
        db_session,
        ElectionStatus.DRAFT,
        name="Draft details election",
    )

    response = client.get(f"/api/elections/{draft_election.id}")

    assert response.status_code == 404


def test_get_election_by_expired_active_id_returns_404(
    client: TestClient,
    db_session: Session,
) -> None:
    now = datetime.now(timezone.utc)
    expired_election = create_election(
        db_session,
        ElectionStatus.ACTIVE,
        name="Expired active election",
        starts_at=now - timedelta(days=2),
        ends_at=now - timedelta(days=1),
    )

    response = client.get(f"/api/elections/{expired_election.id}")

    assert response.status_code == 404


def test_list_candidates_for_active_election_returns_candidates(
    client: TestClient,
    db_session: Session,
) -> None:
    active_election = create_election(
        db_session,
        ElectionStatus.ACTIVE,
        name="Active candidate election",
    )
    first_candidate = create_candidate(
        db_session,
        active_election.id,
        name="First candidate",
    )
    second_candidate = create_candidate(
        db_session,
        active_election.id,
        name="Second candidate",
    )

    response = client.get(f"/api/elections/{active_election.id}/candidates")

    assert response.status_code == 200
    candidate_ids = [candidate["id"] for candidate in response.json()]
    assert candidate_ids == [first_candidate.id, second_candidate.id]


def test_list_candidates_for_draft_election_returns_404(
    client: TestClient,
    db_session: Session,
) -> None:
    draft_election = create_election(
        db_session,
        ElectionStatus.DRAFT,
        name="Draft candidate election",
    )
    create_candidate(db_session, draft_election.id)

    response = client.get(f"/api/elections/{draft_election.id}/candidates")

    assert response.status_code == 404


def test_create_vote_accepts_valid_vote_for_active_election(
    client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        voting_service.zkp_service,
        "verify_proof",
        lambda proof, public_signals: True,
    )
    active_election = create_election(db_session, ElectionStatus.ACTIVE)
    candidate = create_candidate(db_session, active_election.id)

    response = client.post(
        f"/api/elections/{active_election.id}/vote",
        json=build_vote_payload(candidate.id, active_election.id, active_election.merkle_root),
    )

    assert response.status_code == 201
    assert response.json()["election_id"] == active_election.id
    assert response.json()["candidate_id"] == candidate.id
    assert response.json()["nullifier_hash"] == "nullifier-1"


def test_create_vote_rejects_duplicate_nullifier(
    client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        voting_service.zkp_service,
        "verify_proof",
        lambda proof, public_signals: True,
    )
    active_election = create_election(db_session, ElectionStatus.ACTIVE)
    candidate = create_candidate(db_session, active_election.id)
    payload = build_vote_payload(
        candidate.id,
        active_election.id,
        active_election.merkle_root,
        nullifier_hash="same-nullifier",
    )

    first_response = client.post(
        f"/api/elections/{active_election.id}/vote",
        json=payload,
    )
    second_response = client.post(
        f"/api/elections/{active_election.id}/vote",
        json=payload,
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409


def test_create_vote_rejects_invalid_proof(
    client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        voting_service.zkp_service,
        "verify_proof",
        lambda proof, public_signals: False,
    )
    active_election = create_election(db_session, ElectionStatus.ACTIVE)
    candidate = create_candidate(db_session, active_election.id)

    response = client.post(
        f"/api/elections/{active_election.id}/vote",
        json=build_vote_payload(candidate.id, active_election.id, active_election.merkle_root),
    )

    assert response.status_code == 400


def test_create_vote_rejects_candidate_from_other_election(
    client: TestClient,
    db_session: Session,
) -> None:
    target_election = create_election(
        db_session,
        ElectionStatus.ACTIVE,
        name="Target election",
    )
    other_election = create_election(
        db_session,
        ElectionStatus.ACTIVE,
        name="Other election",
    )
    other_candidate = create_candidate(db_session, other_election.id)

    response = client.post(
        f"/api/elections/{target_election.id}/vote",
        json=build_vote_payload(
            other_candidate.id,
            target_election.id,
            target_election.merkle_root,
        ),
    )

    assert response.status_code == 404


def test_create_vote_rejects_public_signals_with_wrong_election_id(
    client: TestClient,
    db_session: Session,
) -> None:
    active_election = create_election(db_session, ElectionStatus.ACTIVE)
    candidate = create_candidate(db_session, active_election.id)
    payload = build_vote_payload(
        candidate.id,
        active_election.id,
        active_election.merkle_root,
    )
    payload["public_signals"]["election_id"] = active_election.id + 1

    response = client.post(
        f"/api/elections/{active_election.id}/vote",
        json=payload,
    )

    assert response.status_code == 400


def test_create_vote_rejects_public_signals_with_wrong_merkle_root(
    client: TestClient,
    db_session: Session,
) -> None:
    active_election = create_election(db_session, ElectionStatus.ACTIVE)
    candidate = create_candidate(db_session, active_election.id)
    payload = build_vote_payload(
        candidate.id,
        active_election.id,
        active_election.merkle_root,
    )
    payload["public_signals"]["merkle_root"] = "wrong-root"

    response = client.post(
        f"/api/elections/{active_election.id}/vote",
        json=payload,
    )

    assert response.status_code == 400


def test_create_vote_rejects_expired_active_election(
    client: TestClient,
    db_session: Session,
) -> None:
    now = datetime.now(timezone.utc)
    expired_election = create_election(
        db_session,
        ElectionStatus.ACTIVE,
        starts_at=now - timedelta(days=2),
        ends_at=now - timedelta(days=1),
    )
    candidate = create_candidate(db_session, expired_election.id)

    response = client.post(
        f"/api/elections/{expired_election.id}/vote",
        json=build_vote_payload(
            candidate.id,
            expired_election.id,
            expired_election.merkle_root,
        ),
    )

    assert response.status_code == 404
