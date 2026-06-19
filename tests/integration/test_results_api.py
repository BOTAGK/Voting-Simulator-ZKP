from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Candidate, Election, ElectionStatus, Vote, VoterToken


def create_election(
    db_session: Session,
    status: ElectionStatus,
    name: str = "Results election",
) -> Election:
    election = Election(
        name=name,
        description=f"{name} description",
        status=status,
    )
    db_session.add(election)
    db_session.commit()
    db_session.refresh(election)

    return election


def create_candidate(
    db_session: Session,
    election_id: int,
    name: str,
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


def create_vote(
    db_session: Session,
    election_id: int,
    candidate_id: int,
    nullifier_hash: str,
) -> Vote:
    vote = Vote(
        election_id=election_id,
        candidate_id=candidate_id,
        nullifier_hash=nullifier_hash,
        proof_json='{"proof": "demo"}',
        public_signals_json='{"signals": ["demo"]}',
    )
    db_session.add(vote)
    db_session.commit()
    db_session.refresh(vote)

    return vote


def create_voter_token(
    db_session: Session,
    election_id: int,
    token_hash: str,
    merkle_index: int,
) -> VoterToken:
    voter_token = VoterToken(
        election_id=election_id,
        token_hash=token_hash,
        merkle_index=merkle_index,
        merkle_path_json=None,
        label_for_admin=None,
    )
    db_session.add(voter_token)
    db_session.commit()
    db_session.refresh(voter_token)

    return voter_token


def test_public_results_returns_closed_election_results(
    client: TestClient,
    db_session: Session,
) -> None:
    election = create_election(db_session, ElectionStatus.CLOSED)
    first_candidate = create_candidate(db_session, election.id, "First candidate")
    second_candidate = create_candidate(db_session, election.id, "Second candidate")
    create_vote(db_session, election.id, first_candidate.id, "nullifier-1")
    create_vote(db_session, election.id, second_candidate.id, "nullifier-2")
    create_vote(db_session, election.id, second_candidate.id, "nullifier-3")
    create_voter_token(db_session, election.id, "token-1", 0)
    create_voter_token(db_session, election.id, "token-2", 1)
    create_voter_token(db_session, election.id, "token-3", 2)

    response = client.get(f"/api/elections/{election.id}/results")

    assert response.status_code == 200
    body = response.json()
    assert body["election_id"] == election.id
    assert body["status"] == ElectionStatus.CLOSED.value
    assert body["total_votes"] == 3
    assert body["total_tokens"] == 3
    assert body["turnout"] == 1.0
    assert body["results"] == [
        {
            "candidate_id": first_candidate.id,
            "candidate_name": first_candidate.name,
            "votes": 1,
        },
        {
            "candidate_id": second_candidate.id,
            "candidate_name": second_candidate.name,
            "votes": 2,
        },
    ]


def test_public_results_rejects_active_election(
    client: TestClient,
    db_session: Session,
) -> None:
    election = create_election(db_session, ElectionStatus.ACTIVE)

    response = client.get(f"/api/elections/{election.id}/results")

    assert response.status_code == 404


def test_admin_results_returns_active_election_results_with_turnout(
    admin_client: TestClient,
    db_session: Session,
) -> None:
    election = create_election(db_session, ElectionStatus.ACTIVE)
    candidate = create_candidate(db_session, election.id, "Candidate")
    create_vote(db_session, election.id, candidate.id, "nullifier-1")
    create_voter_token(db_session, election.id, "token-1", 0)
    create_voter_token(db_session, election.id, "token-2", 1)

    response = admin_client.get(f"/api/admin/elections/{election.id}/results")

    assert response.status_code == 200
    body = response.json()
    assert body["election_id"] == election.id
    assert body["status"] == ElectionStatus.ACTIVE.value
    assert body["total_votes"] == 1
    assert body["total_tokens"] == 2
    assert body["turnout"] == 0.5
