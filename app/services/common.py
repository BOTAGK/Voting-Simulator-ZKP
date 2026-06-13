from sqlalchemy.orm import Session

from app.core.exceptions import ElectionNotFoundError, InvalidElectionStatusError
from app.models.election import Election, ElectionStatus
from app.repositories import election_repository


def get_existing_election(db: Session, election_id: int) -> Election:
    election: Election = election_repository.get_election_by_id(db, election_id)

    if election is None:
        raise ElectionNotFoundError("Election not found.")

    return election


def ensure_election_is_draft(election: Election) -> None:
    if election.status != ElectionStatus.DRAFT:
        raise InvalidElectionStatusError(
            "Candidates can only be added to draft elections."
        )
    
def ensure_election_is_active(election: Election) -> None:
    if election.status != ElectionStatus.ACTIVE:
        raise InvalidElectionStatusError("Election must be active.")


def ensure_election_is_closed(election: Election) -> None:
    if election.status != ElectionStatus.CLOSED:
        raise InvalidElectionStatusError("Election must be closed.")    
