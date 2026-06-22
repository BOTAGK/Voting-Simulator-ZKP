"""Unit tests for voting service business rules."""

import pytest
from sqlalchemy.orm import Session

from app.core.exceptions import (
    CandidateNotFoundError,
    DuplicateNullifierError,
    ElectionNotFoundError,
    InvalidProofError,
)
from app.models import Candidate, Election, ElectionStatus, Vote
from app.schemas.vote import VoteCreate
from app.services import voting_service


def create_election(
    db_session: Session,
    status: ElectionStatus,
    name: str = "Voting service election",
) -> Election:
    election = Election(
        name=name,
        description=f"{name} description",
        status=status,
        merkle_root="test-merkle-root",
    )
    db_session.add(election)
    db_session.commit()
    db_session.refresh(election)

    return election


def create_candidate(
    db_session: Session,
    election_id: int,
    name: str = "Voting service candidate",
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


def build_vote_data(
    candidate_id: int,
    election_id: int,
    merkle_root: str,
    nullifier_hash: str = "nullifier-1",
) -> VoteCreate:
    return VoteCreate(
        candidate_id=candidate_id,
        nullifier_hash=nullifier_hash,
        proof={"proof": "demo"},
        public_signals={
            "election_id": election_id,
            "merkle_root": merkle_root,
            "nullifier_hash": nullifier_hash,
        },
    )


def test_create_vote_saves_valid_vote(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        voting_service.zkp_service,
        "verify_proof",
        lambda proof, public_signals: True,
    )
    election = create_election(db_session, ElectionStatus.ACTIVE)
    candidate = create_candidate(db_session, election.id)
    vote_data = build_vote_data(candidate.id, election.id, election.merkle_root)

    vote = voting_service.create_vote(db_session, election.id, vote_data)

    stored_vote = db_session.get(Vote, vote.id)
    assert stored_vote is not None
    assert stored_vote.election_id == election.id
    assert stored_vote.candidate_id == candidate.id
    assert stored_vote.nullifier_hash == "nullifier-1"


def test_create_vote_rejects_duplicate_nullifier(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        voting_service.zkp_service,
        "verify_proof",
        lambda proof, public_signals: True,
    )
    election = create_election(db_session, ElectionStatus.ACTIVE)
    candidate = create_candidate(db_session, election.id)
    vote_data = build_vote_data(
        candidate.id,
        election.id,
        election.merkle_root,
        nullifier_hash="same-nullifier",
    )
    voting_service.create_vote(db_session, election.id, vote_data)

    with pytest.raises(DuplicateNullifierError, match="already voted"):
        voting_service.create_vote(db_session, election.id, vote_data)


def test_create_vote_rejects_candidate_from_other_election(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        voting_service.zkp_service,
        "verify_proof",
        lambda proof, public_signals: True,
    )
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
    vote_data = build_vote_data(
        other_candidate.id,
        target_election.id,
        target_election.merkle_root,
    )

    with pytest.raises(CandidateNotFoundError, match="Candidate not found"):
        voting_service.create_vote(db_session, target_election.id, vote_data)


def test_create_vote_rejects_vote_in_draft_election(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        voting_service.zkp_service,
        "verify_proof",
        lambda proof, public_signals: True,
    )
    election = create_election(db_session, ElectionStatus.DRAFT)
    candidate = create_candidate(db_session, election.id)
    vote_data = build_vote_data(candidate.id, election.id, election.merkle_root)

    with pytest.raises(ElectionNotFoundError, match="Active election"):
        voting_service.create_vote(db_session, election.id, vote_data)


def test_create_vote_rejects_vote_in_closed_election(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        voting_service.zkp_service,
        "verify_proof",
        lambda proof, public_signals: True,
    )
    election = create_election(db_session, ElectionStatus.CLOSED)
    candidate = create_candidate(db_session, election.id)
    vote_data = build_vote_data(candidate.id, election.id, election.merkle_root)

    with pytest.raises(ElectionNotFoundError, match="Active election"):
        voting_service.create_vote(db_session, election.id, vote_data)


def test_create_vote_rejects_invalid_proof(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        voting_service.zkp_service,
        "verify_proof",
        lambda proof, public_signals: False,
    )
    election = create_election(db_session, ElectionStatus.ACTIVE)
    candidate = create_candidate(db_session, election.id)
    vote_data = build_vote_data(candidate.id, election.id, election.merkle_root)

    with pytest.raises(InvalidProofError, match="Invalid vote proof"):
        voting_service.create_vote(db_session, election.id, vote_data)


def test_create_vote_rejects_public_signals_with_wrong_nullifier(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        voting_service.zkp_service,
        "verify_proof",
        lambda proof, public_signals: True,
    )
    election = create_election(db_session, ElectionStatus.ACTIVE)
    candidate = create_candidate(db_session, election.id)
    vote_data = build_vote_data(candidate.id, election.id, election.merkle_root)
    vote_data.public_signals = vote_data.public_signals.model_copy(
        update={"nullifier_hash": "wrong-nullifier"},
    )

    with pytest.raises(InvalidProofError, match="Public signals"):
        voting_service.create_vote(db_session, election.id, vote_data)


def test_create_vote_rejects_public_signals_with_wrong_merkle_root(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        voting_service.zkp_service,
        "verify_proof",
        lambda proof, public_signals: True,
    )
    election = create_election(db_session, ElectionStatus.ACTIVE)
    candidate = create_candidate(db_session, election.id)
    vote_data = build_vote_data(candidate.id, election.id, election.merkle_root)
    vote_data.public_signals = vote_data.public_signals.model_copy(
        update={"merkle_root": "wrong-root"},
    )

    with pytest.raises(InvalidProofError, match="Public signals"):
        voting_service.create_vote(db_session, election.id, vote_data)
