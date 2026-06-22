import json
from pathlib import Path

import pytest

from app.schemas.voter_token import MerkleProofSchema, VoterTokenPackage
from scripts import extract_token


def build_token_package(token_secret: str, merkle_index: int) -> VoterTokenPackage:
    return VoterTokenPackage(
        election_id=1,
        token_secret=token_secret,
        merkle_root="123",
        merkle_index=merkle_index,
        merkle_proof=MerkleProofSchema(
            siblings=["10", "20"],
            path_indices=[0, 1],
        ),
    )


def test_extract_token_package_writes_selected_token(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "tokens.json"
    output_path = tmp_path / "selected.json"
    packages = [
        build_token_package("111", 0),
        build_token_package("222", 1),
    ]
    input_path.write_text(
        json.dumps([package.model_dump(mode="json") for package in packages]),
        encoding="utf-8",
    )

    selected_package = extract_token.extract_token_package(
        input_path=input_path,
        output_path=output_path,
        index=1,
    )

    saved_data = json.loads(output_path.read_text(encoding="utf-8"))

    assert selected_package.token_secret == "222"
    assert saved_data["token_secret"] == "222"
    assert saved_data["merkle_index"] == 1


def test_extract_token_package_accepts_single_token_json(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "token.json"
    output_path = tmp_path / "selected.json"
    package = build_token_package("333", 0)
    input_path.write_text(
        json.dumps(package.model_dump(mode="json")),
        encoding="utf-8",
    )

    selected_package = extract_token.extract_token_package(
        input_path=input_path,
        output_path=output_path,
        index=0,
    )

    assert selected_package.token_secret == "333"
    assert output_path.exists()


def test_extract_token_package_rejects_invalid_index(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "tokens.json"
    output_path = tmp_path / "selected.json"
    package = build_token_package("111", 0)
    input_path.write_text(
        json.dumps([package.model_dump(mode="json")]),
        encoding="utf-8",
    )

    with pytest.raises(IndexError, match="out of range"):
        extract_token.extract_token_package(
            input_path=input_path,
            output_path=output_path,
            index=5,
        )
