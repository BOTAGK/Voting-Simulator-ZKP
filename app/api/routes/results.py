from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.schemas.results import ElectionResultsRead
from app.services import tally_service
from app.utils.csv import build_election_results_csv

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


@router.get(
    "/{election_id}/results/csv",
    response_class=PlainTextResponse,
)
def export_election_results_csv(
    election_id: int,
    db: Session = Depends(get_db),
) -> PlainTextResponse:
    results = tally_service.get_public_election_results(db, election_id)
    csv_content = build_election_results_csv(results)

    return PlainTextResponse(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": (
                f'attachment; filename="election-{election_id}-results.csv"'
            ),
        },
    )
