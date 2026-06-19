from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.models import Vote
from app.schemas.vote import VoteCreate

def create_vote(db: Session, election_id: int, data: VoteCreate) -> Vote:
    vote: Vote = Vote(election_id=election_id, **data.model_dump())

    db.add(vote)
    db.commit()
    db.refresh(vote)

    return vote

def list_votes_by_election(db: Session, election_id: int) -> list[Vote]:
    statement = (
        select(Vote)
        .where(Vote.election_id == election_id)
        .order_by(Vote.created_at.desc())
    )

    return list(db.scalars(statement).all())

def get_vote_by_id(db: Session, vote_id: int) -> Vote | None:
    return db.get(Vote, vote_id)

def get_vote_by_nullifier_hash(
    db: Session, 
    election_id: int, 
    nullifier_hash: str
) -> Vote | None:
    statement = (
        select(Vote)
        .where(
            Vote.election_id == election_id,
            Vote.nullifier_hash == nullifier_hash,
        )
    )

    return db.scalars(statement).first()

def count_votes_by_candidate(db: Session, election_id: int) -> dict[int, int]:
    statement = (
        select(Vote.candidate_id, func.count(Vote.id))
        .where(Vote.election_id == election_id)
        .group_by(Vote.candidate_id)
    )

    results = db.execute(statement).all()

    return {candidate_id: count for candidate_id, count in results}
