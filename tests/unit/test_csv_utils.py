import csv
import json
from io import StringIO

import pytest

from app.core.exceptions import InvalidCsvError
from app.schemas.results import CandidateResultRead, ElectionResultsRead
from app.schemas.voter_token import MerkleProofSchema, VoterTokenPackage
from app.utils.csv import (
    CSV_EXPORT_DELIMITER,
    build_election_results_csv,
    build_voter_token_packages_csv,
    parse_candidates_csv,
)


def test_parse_candidates_csv_returns_candidate_schemas() -> None:
    candidates = parse_candidates_csv(
        b"name,description\nFirst candidate,First description\nSecond candidate,\n"
    )

    assert len(candidates) == 2
    assert candidates[0].name == "First candidate"
    assert candidates[0].description == "First description"
    assert candidates[1].name == "Second candidate"
    assert candidates[1].description is None


def test_parse_candidates_csv_accepts_semicolon_delimiter() -> None:
    candidates = parse_candidates_csv(
        "name;description\nJan Kowalski;Candidate description\n".encode("utf-8")
    )

    assert candidates[0].name == "Jan Kowalski"
    assert candidates[0].description == "Candidate description"


def test_parse_candidates_csv_normalizes_header_whitespace() -> None:
    candidates = parse_candidates_csv(
        b" name , description \nWhitespace candidate,Whitespace description\n"
    )

    assert candidates[0].name == "Whitespace candidate"
    assert candidates[0].description == "Whitespace description"


def test_parse_candidates_csv_rejects_missing_name_column() -> None:
    with pytest.raises(InvalidCsvError, match="name"):
        parse_candidates_csv(b"description\nNo name column\n")


def test_parse_candidates_csv_rejects_rows_with_too_many_values() -> None:
    with pytest.raises(InvalidCsvError, match="more values than the header"):
        parse_candidates_csv(b"name,description\nCandidate,Description,Extra\n")


def test_parse_candidates_csv_rejects_empty_candidate_list() -> None:
    with pytest.raises(InvalidCsvError, match="does not contain any candidates"):
        parse_candidates_csv(b"name,description\n,\n")


def test_build_voter_token_packages_csv_serializes_token_packages() -> None:
    package = VoterTokenPackage(
        election_id=7,
        token_secret="123",
        merkle_root="999",
        merkle_index=0,
        merkle_proof=MerkleProofSchema(
            siblings=["11", "22"],
            path_indices=[0, 1],
        ),
    )

    csv_content = build_voter_token_packages_csv([package])
    rows = list(csv.DictReader(StringIO(csv_content), delimiter=CSV_EXPORT_DELIMITER))

    assert csv_content.startswith("election_id;token_secret;")
    assert rows == [
        {
            "election_id": "7",
            "token_secret": "123",
            "merkle_root": "999",
            "merkle_index": "0",
            "merkle_siblings": json.dumps(["11", "22"]),
            "merkle_path_indices": json.dumps([0, 1]),
        }
    ]


def test_build_election_results_csv_serializes_candidate_results() -> None:
    results = ElectionResultsRead(
        election_id=3,
        election_name="Demo election",
        status="closed",
        total_votes=5,
        total_tokens=10,
        turnout=0.5,
        results=[
            CandidateResultRead(
                candidate_id=1,
                candidate_name="First candidate",
                votes=2,
            ),
            CandidateResultRead(
                candidate_id=2,
                candidate_name="Second candidate",
                votes=3,
            ),
        ],
    )

    csv_content = build_election_results_csv(results)
    rows = list(csv.DictReader(StringIO(csv_content), delimiter=CSV_EXPORT_DELIMITER))

    assert csv_content.startswith("election_id;election_name;")
    assert rows == [
        {
            "election_id": "3",
            "election_name": "Demo election",
            "status": "closed",
            "total_votes": "5",
            "total_tokens": "10",
            "turnout": "0.5",
            "candidate_id": "1",
            "candidate_name": "First candidate",
            "votes": "2",
        },
        {
            "election_id": "3",
            "election_name": "Demo election",
            "status": "closed",
            "total_votes": "5",
            "total_tokens": "10",
            "turnout": "0.5",
            "candidate_id": "2",
            "candidate_name": "Second candidate",
            "votes": "3",
        },
    ]
