"""Unit tests for election result tallying."""

import pytest
from sqlalchemy.orm import Session

from app.core.exceptions import ElectionNotFoundError
from app.models import Candidate, ElectionStatus, Vote, VoterToken
from app.services import tally_service


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


def dump_schema(value):
    if hasattr(value, "model_dump"):
        return value.model_dump()

    return value


def test_count_votes_includes_candidates_without_votes(
    db_session: Session,
    create_db_election,
) -> None:
    election = create_db_election(status=ElectionStatus.CLOSED)
    first_candidate = create_candidate(db_session, election.id, "First candidate")
    second_candidate = create_candidate(db_session, election.id, "Second candidate")
    create_vote(db_session, election.id, first_candidate.id, "nullifier-1")
    create_vote(db_session, election.id, first_candidate.id, "nullifier-2")

    vote_counts = tally_service.count_votes(db_session, election.id)

    assert vote_counts == {
        first_candidate.id: 2,
        second_candidate.id: 0,
    }


def test_count_votes_rejects_missing_election(db_session: Session) -> None:
    with pytest.raises(ElectionNotFoundError, match="Election not found"):
        tally_service.count_votes(db_session, election_id=999)


def test_get_election_results_returns_candidates_and_total_votes(
    db_session: Session,
    create_db_election,
) -> None:
    election = create_db_election(status=ElectionStatus.CLOSED)
    first_candidate = create_candidate(db_session, election.id, "First candidate")
    second_candidate = create_candidate(db_session, election.id, "Second candidate")
    create_vote(db_session, election.id, first_candidate.id, "nullifier-1")
    create_vote(db_session, election.id, second_candidate.id, "nullifier-2")
    create_vote(db_session, election.id, second_candidate.id, "nullifier-3")

    results = dump_schema(tally_service.get_election_results(db_session, election.id))

    assert results["election_id"] == election.id
    assert results["election_name"] == election.name
    assert results["status"] == ElectionStatus.CLOSED.value
    assert results["total_votes"] == 3
    assert results["results"] == [
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


def test_get_turnout_returns_vote_to_token_ratio(
    db_session: Session,
    create_db_election,
) -> None:
    election = create_db_election(status=ElectionStatus.CLOSED)
    candidate = create_candidate(db_session, election.id, "Candidate")
    create_vote(db_session, election.id, candidate.id, "nullifier-1")
    create_vote(db_session, election.id, candidate.id, "nullifier-2")

    for index in range(4):
        create_voter_token(
            db_session,
            election.id,
            token_hash=f"token-hash-{index}",
            merkle_index=index,
        )

    turnout = tally_service.get_turnout(db_session, election.id)

    assert turnout == pytest.approx(0.5)


def test_get_turnout_returns_zero_when_no_tokens(
    db_session: Session,
    create_db_election,
) -> None:
    election = create_db_election(status=ElectionStatus.CLOSED)
    candidate = create_candidate(db_session, election.id, "Candidate")
    create_vote(db_session, election.id, candidate.id, "nullifier-1")

    turnout = tally_service.get_turnout(db_session, election.id)

    assert turnout == 0.0


def test_get_turnout_percentage_returns_percentage_value(
    db_session: Session,
    create_db_election,
) -> None:
    election = create_db_election(status=ElectionStatus.CLOSED)
    candidate = create_candidate(db_session, election.id, "Candidate")
    create_vote(db_session, election.id, candidate.id, "nullifier-1")

    for index in range(4):
        create_voter_token(
            db_session,
            election.id,
            token_hash=f"token-hash-{index}",
            merkle_index=index,
        )

    turnout_percentage = tally_service.get_turnout_percentage(db_session, election.id)

    assert turnout_percentage == pytest.approx(25.0)
