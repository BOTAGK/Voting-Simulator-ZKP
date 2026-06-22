import json
from pathlib import Path

from app.schemas.vote import VoteCreate
from app.schemas.voter_token import VoterTokenPackage
from app.zkp.proof_models import VoteCircuitInput
from app.zkp.snarkjs_client import GeneratedProof
from scripts import voter_client


def build_voter_package() -> VoterTokenPackage:
    return VoterTokenPackage.model_validate(
        {
            "election_id": 7,
            "token_secret": "123",
            "merkle_root": "999999",
            "merkle_index": 2,
            "merkle_proof": {
                "siblings": ["111", "222", "333"],
                "path_indices": [0, 1, 0],
            },
        }
    )


def test_build_circuit_input_matches_circom_input_shape() -> None:
    voter_package = build_voter_package()

    circuit_input = voter_client.build_circuit_input(voter_package)

    assert circuit_input == VoteCircuitInput(
        token_secret="123",
        merkle_siblings=["111", "222", "333"],
        merkle_path_indices=["0", "1", "0"],
        election_id="7",
        merkle_root="999999",
    )


def test_build_vote_payload_generates_real_proof_payload(monkeypatch) -> None:
    voter_package = build_voter_package()
    captured_circuit_input: dict | None = None

    def fake_generate_groth16_proof(input_data: dict) -> GeneratedProof:
        nonlocal captured_circuit_input
        captured_circuit_input = input_data

        return GeneratedProof(
            proof={"pi_a": ["1", "2", "1"]},
            public_signals=["456", "7", "999999"],
        )

    monkeypatch.setattr(
        voter_client,
        "generate_groth16_proof",
        fake_generate_groth16_proof,
    )

    vote_payload = voter_client.build_vote_payload(
        voter_package,
        candidate_id=42,
    )

    assert vote_payload == VoteCreate(
        candidate_id=42,
        nullifier_hash="456",
        proof={"pi_a": ["1", "2", "1"]},
        public_signals={
            "election_id": 7,
            "merkle_root": "999999",
            "nullifier_hash": "456",
        },
    )
    assert captured_circuit_input == {
        "token_secret": "123",
        "merkle_siblings": ["111", "222", "333"],
        "merkle_path_indices": ["0", "1", "0"],
        "election_id": "7",
        "merkle_root": "999999",
    }


def test_load_voter_package_reads_json_file(tmp_path: Path) -> None:
    package_path = tmp_path / "voter_package.json"
    package_path.write_text(
        json.dumps(build_voter_package().model_dump(mode="json")),
        encoding="utf-8",
    )

    voter_package = voter_client.load_voter_package(package_path)

    assert voter_package == build_voter_package()


def test_save_vote_payload_writes_json_file(tmp_path: Path) -> None:
    output_path = tmp_path / "nested" / "vote_payload.json"
    vote_payload = VoteCreate(
        candidate_id=42,
        nullifier_hash="456",
        proof={"pi_a": ["1", "2", "1"]},
        public_signals={
            "election_id": 7,
            "merkle_root": "999999",
            "nullifier_hash": "456",
        },
    )

    voter_client.save_vote_payload(output_path, vote_payload)

    assert json.loads(output_path.read_text(encoding="utf-8")) == {
        "candidate_id": 42,
        "nullifier_hash": "456",
        "proof": {"pi_a": ["1", "2", "1"]},
        "public_signals": {
            "election_id": 7,
            "merkle_root": "999999",
            "nullifier_hash": "456",
        },
    }
