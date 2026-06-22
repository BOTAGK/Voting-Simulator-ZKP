from sqlalchemy.orm import Session

from app.core.exceptions import CandidateNotFoundError
from app.models import Candidate, Election
from app.repositories import candidate_repository
from app.schemas.candidate import CandidateCreate, CandidateUpdate
from app.services.common import ensure_election_is_draft, get_existing_election
from app.utils.csv import parse_candidates_csv


def add_candidate_to_election(
    db: Session,
    election_id: int,
    candidate_data: CandidateCreate,
) -> Candidate:
    election: Election = get_existing_election(db, election_id)
    ensure_election_is_draft(election)

    return candidate_repository.create_candidate(db, candidate_data, election_id)


def list_candidates_for_election(db: Session, election_id: int) -> list[Candidate]:
    get_existing_election(db, election_id)

    return candidate_repository.list_candidates_by_election(db, election_id)


def get_candidate_details(
    db: Session,
    election_id: int,
    candidate_id: int,
) -> Candidate:
    candidate: Candidate = candidate_repository.get_candidate_for_election_by_id(
        db,
        election_id,
        candidate_id,
    )

    if candidate is None:
        raise CandidateNotFoundError("Candidate not found.")

    return candidate


def update_candidate(
    db: Session, election_id: int, candidate_id: int, data: CandidateUpdate
) -> Candidate:
    election: Election = get_existing_election(db, election_id)
    ensure_election_is_draft(election)

    candidate: Candidate = get_candidate_details(db, election_id, candidate_id)

    return candidate_repository.update_candidate(db, candidate, data)


def delete_candidate(
    db: Session,
    election_id: int,
    candidate_id: int,
) -> None:
    election: Election = get_existing_election(db, election_id)
    ensure_election_is_draft(election)

    candidate: Candidate = get_candidate_details(db, election_id, candidate_id)

    candidate_repository.delete_candidate(db, candidate)


def import_candidates_from_csv(
    db: Session,
    election_id: int,
    file_content: bytes,
) -> list[Candidate]:
    election: Election = get_existing_election(db, election_id)
    ensure_election_is_draft(election)
    candidate_data: list[CandidateCreate] = parse_candidates_csv(file_content)

    return [
        candidate_repository.create_candidate(db, candidate, election_id)
        for candidate in candidate_data
    ]
