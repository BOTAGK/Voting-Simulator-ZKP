from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Candidate
from app.schemas.candidate import CandidateCreate, CandidateUpdate

def create_candidate(db: Session, data: CandidateCreate, election_id: int) -> Candidate:
    candidate: Candidate = Candidate(
        **data.model_dump(), election_id=election_id
    )

    db.add(candidate)
    db.commit()
    db.refresh(candidate)

    return candidate

def list_candidates_by_election(db: Session, election_id: int) -> list[Candidate]:
    statement = (
        select(Candidate)
        .where(Candidate.election_id == election_id)
        .order_by(Candidate.id.asc())
    )
    return list(db.scalars(statement).all())

def get_candidate_by_id(db: Session, candidate_id: int) -> Candidate | None:
    return db.get(Candidate, candidate_id)

def get_candidate_for_election_by_id(
    db: Session, election_id: int, candidate_id: int
) -> Candidate | None:
    statement = (
        select(Candidate)
        .where(
            Candidate.election_id == election_id,
            Candidate.id == candidate_id,
        )
    )
    return db.scalars(statement).first()

def update_candidate(
    db: Session,
    candidate: Candidate,
    data: CandidateUpdate,
) -> Candidate:
    
    update_data: dict[str, Any] = data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(candidate, field, value)

    db.commit()
    db.refresh(candidate)

    return candidate

def delete_candidate(db: Session, candidate: Candidate) -> None:
    db.delete(candidate)
    db.commit()
