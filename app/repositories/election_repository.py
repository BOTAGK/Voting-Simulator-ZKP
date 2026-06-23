from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import Election, ElectionStatus
from app.schemas.election import ElectionCreate, ElectionUpdate


def create_election(db: Session, data: ElectionCreate) -> Election:
    election: Election = Election(**data.model_dump())

    db.add(election)
    db.commit()
    db.refresh(election)

    return election

def list_elections(db: Session) -> list[Election]:
    statement = select(Election).order_by(Election.created_at.desc())
    return list(db.scalars(statement).all())

def get_election_by_id(db: Session, election_id: int) -> Election | None:
    return db.get(Election, election_id)

def update_election(
    db: Session,
    election: Election,
    data: ElectionUpdate,
) -> Election:
    
    update_data: dict[str, Any] = data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(election, field, value)

    db.commit()
    db.refresh(election)

    return election

def delete_election(db: Session, election: Election) -> None:
    db.delete(election)
    db.commit()

def list_elections_by_status(db: Session, status: str) -> list[Election]:
    statement = (
        select(Election)
        .where(Election.status == status)
        .order_by(Election.created_at.desc())
    )

    return list(db.scalars(statement).all())

def list_active_elections(db: Session) -> list[Election]:
    return list_elections_by_status(db, ElectionStatus.ACTIVE)

def get_election_by_id_and_status(
    db: Session, election_id: int, status: str
) -> Election | None:
    statement = (
        select(Election)
        .where(Election.id == election_id, Election.status == status)
    )

    return db.scalars(statement).first()
