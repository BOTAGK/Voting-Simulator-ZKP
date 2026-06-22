from sqlalchemy.orm import Session

from app.core.exceptions import (
    CandidateNotFoundError,
    DuplicateNullifierError,
    ElectionNotFoundError,
    InvalidProofError,
)
from app.models import Candidate, Election, ElectionStatus, Vote
from app.repositories import candidate_repository, election_repository, vote_repository
from app.schemas.vote import VoteCreate
from app.services import zkp_service
from app.utils.time import is_within_datetime_window


def list_active_elections(db: Session) -> list[Election]:
    return [
        election
        for election in election_repository.list_active_elections(db)
        if is_within_datetime_window(election.starts_at, election.ends_at)
    ]


def get_active_election_details(
    db: Session,
    election_id: int,
) -> Election:
    election = election_repository.get_election_by_id_and_status(
        db,
        election_id,
        ElectionStatus.ACTIVE,
    )

    if election is None:
        raise ElectionNotFoundError("Active election not found.")

    if not is_within_datetime_window(election.starts_at, election.ends_at):
        raise ElectionNotFoundError("Active election not found.")

    return election


def list_candidates_for_active_election(
    db: Session,
    election_id: int,
) -> list[Candidate]:
    get_active_election_details(db, election_id)

    return candidate_repository.list_candidates_by_election(db, election_id)


def create_vote(
    db: Session,
    election_id: int,
    vote_data: VoteCreate,
) -> Vote:
    election: Election = get_active_election_details(db, election_id)

    candidate: Candidate = candidate_repository.get_candidate_for_election_by_id(
        db,
        election_id,
        vote_data.candidate_id,
    )

    if candidate is None:
        raise CandidateNotFoundError("Candidate not found in active election.")

    zkp_service.validate_public_signals(
        public_signals=vote_data.public_signals,
        election_id=election_id,
        expected_merkle_root=election.merkle_root,
        nullifier_hash=vote_data.nullifier_hash,
    )

    existing_vote: Vote = vote_repository.get_vote_by_nullifier_hash(
        db,
        election_id,
        vote_data.nullifier_hash,
    )

    if existing_vote is not None:
        raise DuplicateNullifierError("This voter has already voted in this election.")

    proof_is_valid: bool = zkp_service.verify_proof(
        vote_data.proof,
        vote_data.public_signals,
    )

    if not proof_is_valid:
        raise InvalidProofError("Invalid vote proof.")

    return vote_repository.create_vote(db, election_id, vote_data)
