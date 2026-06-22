import json
from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Election, ElectionStatus, Vote
from app.schemas.voter_token import MerkleProofSchema, VoterTokenPackage
from scripts import seed_demo


def fake_generate_voter_tokens(
    _db: Session,
    election_id: int,
    data,
) -> list[VoterTokenPackage]:
    return [
        VoterTokenPackage(
            election_id=election_id,
            token_secret=str(1_000 + index),
            merkle_root=f"root-{election_id}",
            merkle_index=index,
            merkle_proof=MerkleProofSchema(
                siblings=[f"sibling-{index}-0", f"sibling-{index}-1"],
                path_indices=[0, 1],
            ),
        )
        for index in range(data.count)
    ]


@pytest.fixture
def fast_seed_demo(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        seed_demo.token_service,
        "generate_voter_tokens",
        fake_generate_voter_tokens,
    )
    monkeypatch.setattr(
        seed_demo,
        "calculate_nullifier_hash",
        lambda package, election_id: f"nullifier-{election_id}-{package.token_secret}",
    )


def list_demo_elections(db_session: Session) -> list[Election]:
    statement = (
        select(Election)
        .where(Election.name.like(f"{seed_demo.DEMO_PREFIX}%"))
        .order_by(Election.id.asc())
    )
    return list(db_session.scalars(statement).all())


def test_seed_demo_data_creates_demo_elections_votes_and_token_files(
    db_session: Session,
    tmp_path: Path,
    fast_seed_demo: None,
) -> None:
    seed_demo.seed_demo_data(db_session, tmp_path)

    elections = list_demo_elections(db_session)

    assert [election.status for election in elections] == [
        ElectionStatus.DRAFT,
        ElectionStatus.ACTIVE,
        ElectionStatus.CLOSED,
    ]
    assert [len(election.candidates) for election in elections] == [3, 3, 3]

    active_election = elections[1]
    closed_election = elections[2]
    active_votes = db_session.scalars(
        select(Vote).where(Vote.election_id == active_election.id)
    ).all()
    closed_votes = db_session.scalars(
        select(Vote).where(Vote.election_id == closed_election.id)
    ).all()

    assert len(active_votes) == 3
    assert len(closed_votes) == 14

    active_available_path = tmp_path / "demo_active_available_tokens.json"
    closed_available_path = tmp_path / "demo_closed_available_tokens.json"

    assert active_available_path.exists()
    assert closed_available_path.exists()
    assert len(json.loads(active_available_path.read_text(encoding="utf-8"))) == 7
    assert len(json.loads(closed_available_path.read_text(encoding="utf-8"))) == 6
    assert (tmp_path / "demo_active_tokens.csv").exists()
    assert (tmp_path / "demo_closed_tokens.csv").exists()


def test_clear_demo_data_removes_only_demo_records_and_demo_files(
    db_session: Session,
    tmp_path: Path,
) -> None:
    demo_election = Election(
        name=f"{seed_demo.DEMO_PREFIX} Temporary demo",
        description="Demo record to remove.",
        status=ElectionStatus.DRAFT,
    )
    regular_election = Election(
        name="Regular election",
        description="Record that must stay.",
        status=ElectionStatus.DRAFT,
    )
    db_session.add_all([demo_election, regular_election])
    db_session.commit()

    demo_file = tmp_path / "demo_active_tokens.json"
    regular_file = tmp_path / "manual_note.txt"
    demo_file.write_text("demo", encoding="utf-8")
    regular_file.write_text("keep", encoding="utf-8")

    seed_demo.clear_demo_data(db_session, tmp_path)

    remaining_elections = list(db_session.scalars(select(Election)).all())

    assert [election.name for election in remaining_elections] == [
        "Regular election"
    ]
    assert not demo_file.exists()
    assert regular_file.exists()


def test_demo_data_exists_detects_seeded_demo_election(
    db_session: Session,
) -> None:
    assert not seed_demo.demo_data_exists(db_session)

    db_session.add(
        Election(
            name=f"{seed_demo.DEMO_PREFIX} Existing demo",
            description="Already seeded.",
            status=ElectionStatus.DRAFT,
        )
    )
    db_session.commit()

    assert seed_demo.demo_data_exists(db_session)


def test_validate_election_seed_rejects_more_votes_than_tokens() -> None:
    election_seed = seed_demo.ElectionSeed(
        name="Broken seed",
        description="Too many votes.",
        status=ElectionStatus.ACTIVE,
        candidates=[seed_demo.CandidateSeed("Candidate", "Description")],
        token_count=1,
        label_prefix="broken",
        vote_distribution=[2],
    )

    with pytest.raises(ValueError, match="more demo votes than generated tokens"):
        seed_demo.validate_election_seed(election_seed)


def test_validate_election_seed_rejects_more_vote_buckets_than_candidates() -> None:
    election_seed = seed_demo.ElectionSeed(
        name="Broken seed",
        description="Too many vote buckets.",
        status=ElectionStatus.ACTIVE,
        candidates=[seed_demo.CandidateSeed("Candidate", "Description")],
        token_count=2,
        label_prefix="broken",
        vote_distribution=[1, 1],
    )

    with pytest.raises(ValueError, match="more vote buckets than candidates"):
        seed_demo.validate_election_seed(election_seed)
