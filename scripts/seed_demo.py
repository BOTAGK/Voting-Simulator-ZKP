from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.database import SessionLocal, init_db
from app.models import Candidate, Election, ElectionStatus, Vote
from app.schemas.voter_token import VoterTokenGenerateRequest, VoterTokenPackage
from app.services import token_service
from app.utils.csv import build_voter_token_packages_csv
from app.zkp.poseidon import poseidon_hash

DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "output" / "demo"
DEMO_PREFIX = "[DEMO]"


@dataclass(frozen=True)
class CandidateSeed:
    name: str
    description: str


@dataclass(frozen=True)
class ElectionSeed:
    name: str
    description: str
    status: ElectionStatus
    candidates: list[CandidateSeed]
    token_count: int
    label_prefix: str
    vote_distribution: list[int]


DRAFT_ELECTION = ElectionSeed(
    name=f"{DEMO_PREFIX} Draft election",
    description="Demo election for presenting administrator workflow.",
    status=ElectionStatus.DRAFT,
    candidates=[
        CandidateSeed("Jan Kowalski", "Candidate prepared for editing."),
        CandidateSeed("Anna Nowak", "Candidate prepared for editing."),
        CandidateSeed("Piotr Zielinski", "Candidate prepared for editing."),
    ],
    token_count=0,
    label_prefix="draft-demo",
    vote_distribution=[],
)

ACTIVE_ELECTION = ElectionSeed(
    name=f"{DEMO_PREFIX} Active voting",
    description="Demo election with a few already submitted votes.",
    status=ElectionStatus.ACTIVE,
    candidates=[
        CandidateSeed("Maria Wisniewska", "Candidate in the active election."),
        CandidateSeed("Tomasz Wojcik", "Candidate in the active election."),
        CandidateSeed("Katarzyna Kaminska", "Candidate in the active election."),
    ],
    token_count=10,
    label_prefix="active-demo",
    vote_distribution=[1, 1, 1],
)

CLOSED_ELECTION = ElectionSeed(
    name=f"{DEMO_PREFIX} Closed election",
    description="Historical demo election with ready-made results.",
    status=ElectionStatus.CLOSED,
    candidates=[
        CandidateSeed("Adam Nowicki", "Candidate in the closed election."),
        CandidateSeed("Ewa Lewandowska", "Candidate in the closed election."),
        CandidateSeed("Michal Zielinski", "Candidate in the closed election."),
    ],
    token_count=20,
    label_prefix="closed-demo",
    vote_distribution=[6, 5, 3],
)

DEMO_ELECTIONS = [
    DRAFT_ELECTION,
    ACTIVE_ELECTION,
    CLOSED_ELECTION,
]


def main() -> None:
    args = parse_args()
    init_db()

    with SessionLocal() as db:
        if args.clear:
            clear_demo_data(db, args.output_dir)
            print("Demo data cleared.")
            return

        if args.reset:
            clear_demo_data(db, args.output_dir)

        if demo_data_exists(db):
            print("Demo data already exists. Use --reset to recreate it.")
            return

        seed_demo_data(db, args.output_dir)
        print("Demo data created.")
        print(f"Token packages saved in: {args.output_dir}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create or clear local demo data for the voting simulator."
    )
    action_group = parser.add_mutually_exclusive_group()
    action_group.add_argument(
        "--reset",
        action="store_true",
        help="Remove existing demo data and create it again.",
    )
    action_group.add_argument(
        "--clear",
        action="store_true",
        help="Remove existing demo data without creating new records.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory where demo token packages will be saved.",
    )

    return parser.parse_args()


def seed_demo_data(db: Session, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    for election_seed in DEMO_ELECTIONS:
        validate_election_seed(election_seed)

        election = create_demo_election(db, election_seed)
        candidates = create_demo_candidates(db, election, election_seed.candidates)
        packages = generate_demo_tokens(db, election, election_seed)

        if election_seed.status != ElectionStatus.DRAFT:
            election.status = election_seed.status
            db.commit()
            db.refresh(election)

        if election_seed.vote_distribution:
            create_demo_votes(
                db=db,
                election=election,
                candidates=candidates,
                packages=packages,
                vote_distribution=election_seed.vote_distribution,
            )

        save_demo_token_packages(
            output_dir=output_dir,
            election_seed=election_seed,
            packages=packages,
        )


def validate_election_seed(election_seed: ElectionSeed) -> None:
    if len(election_seed.vote_distribution) > len(election_seed.candidates):
        raise ValueError(f"{election_seed.name} has more vote buckets than candidates.")

    if sum(election_seed.vote_distribution) > election_seed.token_count:
        raise ValueError(
            f"{election_seed.name} assigns more demo votes than generated tokens."
        )


def create_demo_election(db: Session, election_seed: ElectionSeed) -> Election:
    now = datetime.now(timezone.utc)
    election = Election(
        name=election_seed.name,
        description=election_seed.description,
        status=ElectionStatus.DRAFT,
        starts_at=now - timedelta(hours=1),
        ends_at=now + timedelta(days=1),
    )

    if election_seed.status == ElectionStatus.CLOSED:
        election.starts_at = now - timedelta(days=10)
        election.ends_at = now - timedelta(days=9)

    db.add(election)
    db.commit()
    db.refresh(election)

    return election


def create_demo_candidates(
    db: Session,
    election: Election,
    candidates: list[CandidateSeed],
) -> list[Candidate]:
    created_candidates: list[Candidate] = []

    for candidate_seed in candidates:
        candidate = Candidate(
            election_id=election.id,
            name=candidate_seed.name,
            description=candidate_seed.description,
        )
        db.add(candidate)
        created_candidates.append(candidate)

    db.commit()

    for candidate in created_candidates:
        db.refresh(candidate)

    return created_candidates


def generate_demo_tokens(
    db: Session,
    election: Election,
    election_seed: ElectionSeed,
) -> list[VoterTokenPackage]:
    if election_seed.token_count == 0:
        return []

    return token_service.generate_voter_tokens(
        db,
        election.id,
        VoterTokenGenerateRequest(
            count=election_seed.token_count,
            label_prefix=election_seed.label_prefix,
        ),
    )


def create_demo_votes(
    db: Session,
    election: Election,
    candidates: list[Candidate],
    packages: list[VoterTokenPackage],
    vote_distribution: list[int],
) -> None:
    used_package_index = 0

    for candidate, vote_count in zip(candidates, vote_distribution, strict=True):
        for _ in range(vote_count):
            package = packages[used_package_index]
            used_package_index += 1

            nullifier_hash = calculate_nullifier_hash(package, election.id)
            vote = Vote(
                election_id=election.id,
                candidate_id=candidate.id,
                nullifier_hash=nullifier_hash,
                proof_json=json.dumps({"demo": True, "source": "seed_demo"}),
                public_signals_json=json.dumps(
                    {
                        "election_id": election.id,
                        "merkle_root": package.merkle_root,
                        "nullifier_hash": nullifier_hash,
                    }
                ),
            )
            db.add(vote)

    db.commit()


def calculate_nullifier_hash(
    package: VoterTokenPackage,
    election_id: int,
) -> str:
    return str(poseidon_hash([int(package.token_secret), election_id]))


def save_demo_token_packages(
    output_dir: Path,
    election_seed: ElectionSeed,
    packages: list[VoterTokenPackage],
) -> None:
    if not packages:
        return

    base_name = build_output_base_name(election_seed)
    save_token_packages_json(output_dir / f"{base_name}_tokens.json", packages)
    save_token_packages_csv(output_dir / f"{base_name}_tokens.csv", packages)

    used_token_count = sum(election_seed.vote_distribution)
    available_packages = packages[used_token_count:]

    if available_packages:
        save_token_packages_json(
            output_dir / f"{base_name}_available_tokens.json",
            available_packages,
        )
        save_token_packages_csv(
            output_dir / f"{base_name}_available_tokens.csv",
            available_packages,
        )


def build_output_base_name(election_seed: ElectionSeed) -> str:
    if election_seed.status == ElectionStatus.ACTIVE:
        return "demo_active"

    if election_seed.status == ElectionStatus.CLOSED:
        return "demo_closed"

    return "demo_draft"


def save_token_packages_json(
    path: Path,
    packages: list[VoterTokenPackage],
) -> None:
    path.write_text(
        json.dumps(
            [package.model_dump(mode="json") for package in packages],
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def save_token_packages_csv(
    path: Path,
    packages: list[VoterTokenPackage],
) -> None:
    path.write_text(
        build_voter_token_packages_csv(packages),
        encoding="utf-8",
    )


def demo_data_exists(db: Session) -> bool:
    statement = select(Election).where(Election.name.like(f"{DEMO_PREFIX}%"))
    return db.scalars(statement).first() is not None


def clear_demo_data(db: Session, output_dir: Path) -> None:
    statement = select(Election).where(Election.name.like(f"{DEMO_PREFIX}%"))
    demo_elections = list(db.scalars(statement).all())

    for election in demo_elections:
        db.delete(election)

    db.commit()
    clear_demo_output(output_dir)


def clear_demo_output(output_dir: Path) -> None:
    if not output_dir.exists():
        return

    for path in output_dir.glob("demo_*"):
        if path.is_file():
            path.unlink()


if __name__ == "__main__":
    main()
