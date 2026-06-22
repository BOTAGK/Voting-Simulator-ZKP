from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.models import Candidate, Election, Vote
from app.schemas.candidate import CandidateRead
from app.schemas.election import ElectionRead
from app.schemas.vote import VoteCreate, VoteRead
from app.services import voting_service


router = APIRouter(
    prefix="/elections",
    tags=["voting"],
)


@router.get(
    "/active",
    response_model=list[ElectionRead],
)
def list_active_elections(
    db: Session = Depends(get_db),
) -> list[Election]:
    return voting_service.list_active_elections(db)


@router.get(
    "/{election_id}",
    response_model=ElectionRead,
)
def get_active_election(
    election_id: int,
    db: Session = Depends(get_db),
) -> Election:
    return voting_service.get_active_election_details(db, election_id)


@router.get(
    "/{election_id}/candidates",
    response_model=list[CandidateRead],
)
def list_candidates_for_active_election(
    election_id: int,
    db: Session = Depends(get_db),
) -> list[Candidate]:
    return voting_service.list_candidates_for_active_election(db, election_id)


@router.post(
    "/{election_id}/vote",
    response_model=VoteRead,
    status_code=status.HTTP_201_CREATED,
)
def create_vote(
    election_id: int,
    vote_data: VoteCreate,
    db: Session = Depends(get_db),
) -> Vote:
    return voting_service.create_vote(db, election_id, vote_data)
