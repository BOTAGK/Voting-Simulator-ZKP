"""Unit tests for voter token generation service."""

import json

import pytest
from sqlalchemy.orm import Session

import app.services.token_service as token_service
from app.core.exceptions import DuplicateVoterTokenError, InvalidElectionStatusError
from app.models import ElectionStatus, VoterToken
from app.schemas.voter_token import VoterTokenGenerateRequest


pytestmark = pytest.mark.usefixtures("fast_token_generation")


def test_generate_voter_tokens_persists_tokens_and_merkle_root(
    db_session: Session,
    create_db_election,
) -> None:
    election = create_db_election()
    request = VoterTokenGenerateRequest(count=2, label_prefix="voter")

    packages = token_service.generate_voter_tokens(db_session, election.id, request)

    stored_tokens = (
        db_session.query(VoterToken)
        .filter(VoterToken.election_id == election.id)
        .order_by(VoterToken.merkle_index.asc())
        .all()
    )
    db_session.refresh(election)

    assert election.merkle_root == "999999"
    assert len(stored_tokens) == 2
    assert [token.token_hash for token in stored_tokens] == ["1101", "1102"]
    assert [token.merkle_index for token in stored_tokens] == [0, 1]
    assert [token.label_for_admin for token in stored_tokens] == [
        "voter-1",
        "voter-2",
    ]
    assert packages[0].token_secret == "101"
    assert packages[0].merkle_root == "999999"
    assert packages[0].merkle_index == 0
    assert packages[0].merkle_proof.siblings == ["10000", "20000"]
    assert packages[0].merkle_proof.path_indices == [0, 1]


def test_generate_voter_tokens_stores_merkle_path_as_json(
    db_session: Session,
    create_db_election,
) -> None:
    election = create_db_election()
    request = VoterTokenGenerateRequest(count=1)

    [package] = token_service.generate_voter_tokens(db_session, election.id, request)
    stored_token = db_session.query(VoterToken).one()

    assert stored_token.merkle_path_json is not None
    assert json.loads(stored_token.merkle_path_json) == package.merkle_proof.model_dump()


def test_generate_voter_tokens_does_not_store_token_secret(
    db_session: Session,
    create_db_election,
) -> None:
    election = create_db_election()
    request = VoterTokenGenerateRequest(count=1)

    [package] = token_service.generate_voter_tokens(db_session, election.id, request)
    stored_token = db_session.query(VoterToken).one()

    assert package.token_secret == "101"
    assert stored_token.token_hash == "1101"
    assert not hasattr(stored_token, "token_secret")


def test_generate_voter_tokens_rejects_second_generation(
    db_session: Session,
    create_db_election,
) -> None:
    election = create_db_election()
    request = VoterTokenGenerateRequest(count=1)
    token_service.generate_voter_tokens(db_session, election.id, request)

    with pytest.raises(DuplicateVoterTokenError, match="already been generated"):
        token_service.generate_voter_tokens(db_session, election.id, request)


def test_generate_voter_tokens_requires_draft_election(
    db_session: Session,
    create_db_election,
) -> None:
    election = create_db_election(status=ElectionStatus.ACTIVE)
    request = VoterTokenGenerateRequest(count=1)

    with pytest.raises(InvalidElectionStatusError, match="draft elections"):
        token_service.generate_voter_tokens(db_session, election.id, request)
