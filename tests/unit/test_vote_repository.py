import pytest
from sqlalchemy.orm import Session

from app.core.exceptions import DuplicateNullifierError
from app.models import Candidate, Election, ElectionStatus
from app.repositories import vote_repository
from app.schemas.vote import VoteCreate
from app.zkp.proof_models import PublicSignals


def build_vote_create(
    candidate_id: int,
    election_id: int,
    nullifier_hash: str,
) -> VoteCreate:
    return VoteCreate(
        candidate_id=candidate_id,
        nullifier_hash=nullifier_hash,
        proof={"proof": "demo"},
        public_signals=PublicSignals(
            election_id=election_id,
            merkle_root="root",
            nullifier_hash=nullifier_hash,
        ),
    )


def test_create_vote_converts_database_duplicate_to_domain_error(
    db_session: Session,
) -> None:
    election = Election(
        name="Repository duplicate election",
        description="Checks database-level nullifier protection.",
        status=ElectionStatus.ACTIVE,
        merkle_root="root",
    )
    db_session.add(election)
    db_session.commit()
    db_session.refresh(election)

    candidate = Candidate(
        election_id=election.id,
        name="Candidate",
        description=None,
    )
    db_session.add(candidate)
    db_session.commit()
    db_session.refresh(candidate)

    vote_data = build_vote_create(
        candidate_id=candidate.id,
        election_id=election.id,
        nullifier_hash="duplicate-nullifier",
    )

    vote_repository.create_vote(db_session, election.id, vote_data)

    with pytest.raises(DuplicateNullifierError, match="already voted"):
        vote_repository.create_vote(db_session, election.id, vote_data)
