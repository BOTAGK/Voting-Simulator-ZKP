
from fastapi import APIRouter, Depends, status, Response
from sqlalchemy.orm import Session

from app.auth.permissions import require_admin
from app.core.deps import get_db
from app.models import Candidate, Election, VoterToken
from app.schemas.candidate import CandidateCreate, CandidateRead, CandidateUpdate
from app.schemas.election import ElectionCreate, ElectionRead, ElectionUpdate
from app.schemas.results import ElectionResultsRead
from app.schemas.voter_token import VoterTokenPackage, VoterTokenGenerateRequest, VoterTokenRead
from app.services import election_service, candidate_service, tally_service, token_service


router = APIRouter(
    prefix="/admin/elections",
    tags=["admin elections"],
    dependencies=[Depends(require_admin)],
)

@router.post(
    "",
    response_model=ElectionRead,
    status_code=status.HTTP_201_CREATED,
)
def create_election(
    data: ElectionCreate,
    db: Session = Depends(get_db),
) -> Election:
    return election_service.create_new_election(db, data)

@router.get(
    "",
    response_model=list[ElectionRead],
) 
def list_elections(
    db: Session = Depends(get_db),
) -> list[Election]:
    return election_service.list_all_elections(db)

@router.get(
    "/{election_id}",
    response_model=ElectionRead,
)
def get_election(
    election_id: int,
    db: Session = Depends(get_db),
) -> Election:
    return election_service.get_election_details(db, election_id)

@router.patch(
    "/{election_id}",
    response_model=ElectionRead,
)
def update_election(
    election_id: int,
    data: ElectionUpdate,
    db: Session = Depends(get_db),
) -> Election:
    return election_service.update_existing_election(db, election_id, data)

@router.post(
    "/{election_id}/open",
    response_model=ElectionRead,
)
def open_election(
    election_id: int,
    db: Session = Depends(get_db),
) -> Election:
    return election_service.open_election(db, election_id)

@router.post(
    "/{election_id}/close",
    response_model=ElectionRead,
)
def close_election(
    election_id: int,
    db: Session = Depends(get_db),
) -> Election:
    return election_service.close_election(db, election_id)

@router.delete(
    "/{election_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_election(
    election_id: int,
    db: Session = Depends(get_db),
) -> Response:
    election_service.delete_existing_election(db, election_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.post(
    "/{election_id}/candidates",
    response_model=CandidateRead,
    status_code=status.HTTP_201_CREATED,
) 
def add_candidate_to_election(
    election_id: int,
    data: CandidateCreate,
    db: Session = Depends(get_db),
) -> Candidate:
    return candidate_service.add_candidate_to_election(db, election_id, data)

@router.get(
    "/{election_id}/candidates",
    response_model=list[CandidateRead],
)
def list_candidates_for_election(
    election_id: int,
    db: Session = Depends(get_db),
) -> list[Candidate]:
    return candidate_service.list_candidates_for_election(db, election_id)

@router.get(
    "/{election_id}/candidates/{candidate_id}",
    response_model=CandidateRead,
)
def get_candidate_for_election(
    election_id: int,
    candidate_id: int,
    db: Session = Depends(get_db),
) -> Candidate:
    return candidate_service.get_candidate_details(db, election_id, candidate_id)

@router.patch(
    "/{election_id}/candidates/{candidate_id}",
    response_model=CandidateRead,
)
def update_candidate_for_election(
    election_id: int,
    candidate_id: int,
    data: CandidateUpdate,
    db: Session = Depends(get_db),
) -> Candidate:
    return candidate_service.update_candidate(db, election_id, candidate_id, data)

@router.delete(
    "/{election_id}/candidates/{candidate_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_candidate_for_election(
    election_id: int,
    candidate_id: int,
    db: Session = Depends(get_db),
) -> Response:
    candidate_service.delete_candidate(db, election_id, candidate_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.post(
    "/{election_id}/tokens/generate",
    response_model=list[VoterTokenPackage],
    status_code=status.HTTP_201_CREATED,
)
def generate_voter_tokens_for_election(
    election_id: int,
    data: VoterTokenGenerateRequest,
    db: Session = Depends(get_db),
) -> list[VoterTokenPackage]:
    return token_service.generate_voter_tokens(db, election_id, data)

@router.get(
    "/{election_id}/tokens",
    response_model=list[VoterTokenRead],
)
def list_voter_tokens_for_election(
    election_id: int,
    db: Session = Depends(get_db),
) -> list[VoterToken]:
    return token_service.list_voter_tokens_for_election(db, election_id)


@router.get(
    "/{election_id}/results",
    response_model=ElectionResultsRead,
)
def get_election_results_for_admin(
    election_id: int,
    db: Session = Depends(get_db),
) -> ElectionResultsRead:
    return tally_service.get_election_results(db, election_id)
