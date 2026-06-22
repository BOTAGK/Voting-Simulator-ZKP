from sqlalchemy.orm import Session

from app.core.exceptions import ElectionNotFoundError
from app.models import Candidate, Election, ElectionStatus
from app.repositories import (
    candidate_repository,
    election_repository,
    vote_repository,
    voter_token_repository,
)
from app.schemas.results import CandidateResultRead, ElectionResultsRead


def count_votes(db: Session, election_id: int) -> dict[int, int]:
    election: Election | None = election_repository.get_election_by_id(db, election_id)

    if election is None:
        raise ElectionNotFoundError("Election not found.")

    candidates: list[Candidate] = candidate_repository.list_candidates_by_election(
        db,
        election_id,
    )
    vote_counts = vote_repository.count_votes_by_candidate(db, election_id)

    return {candidate.id: vote_counts.get(candidate.id, 0) for candidate in candidates}


def get_election_results(db: Session, election_id: int) -> ElectionResultsRead:
    election: Election | None = election_repository.get_election_by_id(db, election_id)

    if election is None:
        raise ElectionNotFoundError("Election not found.")

    candidates: list[Candidate] = candidate_repository.list_candidates_by_election(
        db,
        election_id,
    )
    vote_counts: dict[int, int] = count_votes(db, election_id)

    candidate_results: list[CandidateResultRead] = [
        CandidateResultRead(
            candidate_id=candidate.id,
            candidate_name=candidate.name,
            votes=vote_counts.get(candidate.id, 0),
        )
        for candidate in candidates
    ]

    total_votes: int = sum(result.votes for result in candidate_results)
    total_tokens: int = len(
        voter_token_repository.list_voter_tokens_by_election(db, election_id)
    )

    return ElectionResultsRead(
        election_id=election.id,
        election_name=election.name,
        status=election.status.value,
        total_votes=total_votes,
        total_tokens=total_tokens,
        turnout=_calculate_turnout(total_votes, total_tokens),
        results=candidate_results,
    )


def get_public_election_results(db: Session, election_id: int) -> ElectionResultsRead:
    election: Election | None = election_repository.get_election_by_id(db, election_id)

    if election is None or election.status != ElectionStatus.CLOSED:
        raise ElectionNotFoundError("Closed election results not found.")

    return get_election_results(db, election_id)


def get_turnout(db: Session, election_id: int) -> float:
    election: Election | None = election_repository.get_election_by_id(db, election_id)

    if election is None:
        raise ElectionNotFoundError("Election not found.")

    total_votes: int = len(vote_repository.list_votes_by_election(db, election_id))
    total_tokens: int = len(
        voter_token_repository.list_voter_tokens_by_election(db, election_id)
    )

    return _calculate_turnout(total_votes, total_tokens)


def get_turnout_percentage(db: Session, election_id: int) -> float:
    turnout: float = get_turnout(db, election_id)
    return turnout * 100


def _calculate_turnout(total_votes: int, total_tokens: int) -> float:
    if total_tokens == 0:
        return 0.0

    return total_votes / total_tokens
