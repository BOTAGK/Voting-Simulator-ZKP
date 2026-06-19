from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.schemas.results import ElectionResultsRead
from app.services import tally_service

router = APIRouter(
    prefix="/elections",
    tags=["results"],
)


@router.get(
    "/{election_id}/results",
    response_model=ElectionResultsRead,
)
def get_election_results(
    election_id: int,
    db: Session = Depends(get_db),
) -> ElectionResultsRead:
    return tally_service.get_public_election_results(db, election_id)
