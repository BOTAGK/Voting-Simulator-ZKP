from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import DuplicateVoterTokenError
from app.models import VoterToken


def create_voter_token(
    db: Session,
    election_id: int,
    token_hash: str,
    merkle_index: int,
    merkle_path_json: str | None,
    label_for_admin: str | None,
) -> VoterToken:
    voter_token: VoterToken = VoterToken(
        election_id=election_id,
        token_hash=token_hash,
        merkle_index=merkle_index,
        merkle_path_json=merkle_path_json,
        label_for_admin=label_for_admin,
    )

    db.add(voter_token)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise DuplicateVoterTokenError(
            "Voter token hash already exists in this election."
        ) from exc

    db.refresh(voter_token)

    return voter_token


def bulk_create_voter_tokens(
    db: Session,
    voter_tokens: list[VoterToken],
) -> list[VoterToken]:
    db.add_all(voter_tokens)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise DuplicateVoterTokenError(
            "Voter token hash already exists in this election."
        ) from exc

    for voter_token in voter_tokens:
        db.refresh(voter_token)

    return voter_tokens


def list_voter_tokens_by_election(db: Session, election_id: int) -> list[VoterToken]:
    statement = (
        select(VoterToken)
        .where(VoterToken.election_id == election_id)
        .order_by(VoterToken.merkle_index.asc())
    )

    return list(db.scalars(statement).all())


def get_voter_token_by_id(db: Session, voter_token_id: int) -> VoterToken | None:
    return db.get(VoterToken, voter_token_id)


def delete_voter_token(db: Session, voter_token: VoterToken) -> None:
    db.delete(voter_token)
    db.commit()


def delete_voter_tokens_by_election(db: Session, election_id: int) -> None:
    statement = select(VoterToken).where(VoterToken.election_id == election_id)
    voter_tokens = db.scalars(statement).all()

    for voter_token in voter_tokens:
        db.delete(voter_token)

    db.commit()


def get_voter_token_by_hash(
    db: Session,
    election_id: int,
    token_hash: str,
) -> VoterToken | None:
    statement = (
        select(VoterToken)
        .where(
            VoterToken.election_id == election_id,
            VoterToken.token_hash == token_hash,
        )
    )

    return db.scalars(statement).first()
