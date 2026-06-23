from datetime import datetime

from sqlalchemy.orm import Session

from app.core.exceptions import (
    ElectionNotFoundError,
    InvalidElectionDatesError,
    InvalidElectionStatusError,
)
from app.models import Election, ElectionStatus
from app.repositories import election_repository
from app.schemas.election import ElectionCreate, ElectionUpdate
from app.utils.time import is_within_datetime_window


def validate_election_dates(
    starts_at: datetime | None,
    ends_at: datetime | None,
) -> None:
    if starts_at is not None and ends_at is not None and ends_at <= starts_at:
        raise InvalidElectionDatesError("Election end date must be after start date.")


def ensure_election_can_be_active(election: Election) -> None:
    if not is_within_datetime_window(election.starts_at, election.ends_at):
        raise InvalidElectionStatusError(
            "Election can only be active between its start and end dates."
        )


def create_new_election(db: Session, data: ElectionCreate) -> Election:
    validate_election_dates(data.starts_at, data.ends_at)

    return election_repository.create_election(db, data)


def list_all_elections(db: Session) -> list[Election]:
    return election_repository.list_elections(db)


def get_election_details(db: Session, election_id: int) -> Election:

    election = election_repository.get_election_by_id(db, election_id)

    if election is None:
        raise ElectionNotFoundError("Election not found.")

    return election

def update_existing_election(
    db: Session, election_id: int, data: ElectionUpdate
) -> Election:
    election = get_election_details(db, election_id)

    starts_at = data.starts_at if data.starts_at is not None else election.starts_at
    ends_at = data.ends_at if data.ends_at is not None else election.ends_at

    validate_election_dates(starts_at, ends_at)

    if election.status != ElectionStatus.DRAFT:
        raise InvalidElectionStatusError("Only draft elections can be updated.")

    return election_repository.update_election(db, election, data)


def delete_existing_election(db: Session, election_id: int) -> None:
    election = get_election_details(db, election_id)

    election_repository.delete_election(db, election)


def open_election(db: Session, election_id: int) -> Election:
    election = get_election_details(db, election_id)

    if election.status != ElectionStatus.DRAFT:
        raise InvalidElectionStatusError("Only draft election can be opened.")

    validate_election_dates(election.starts_at, election.ends_at)
    ensure_election_can_be_active(election)

    election.status = ElectionStatus.ACTIVE
    db.commit()
    db.refresh(election)

    return election
def close_election(db: Session, election_id: int) -> Election:
    election = get_election_details(db, election_id)

    if election.status != ElectionStatus.ACTIVE:
        raise InvalidElectionStatusError("Only active election can be closed.")

    election.status = ElectionStatus.CLOSED
    db.commit()
    db.refresh(election)

    return election


def cancel_draft_election(db: Session, election_id: int) -> Election:
    election = get_election_details(db, election_id)

    if election.status != ElectionStatus.DRAFT:
        raise InvalidElectionStatusError("Only draft election can be cancelled.")

    election.status = ElectionStatus.CLOSED
    db.commit()
    db.refresh(election)

    return election
