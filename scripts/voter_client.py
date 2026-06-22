import argparse
import json
from pathlib import Path

from app.schemas.vote import VoteCreate
from app.schemas.voter_token import VoterTokenPackage
from app.zkp.proof_models import PublicSignals, VoteCircuitInput
from app.zkp.snarkjs_client import GeneratedProof, generate_groth16_proof


def load_voter_package(path: Path) -> VoterTokenPackage:
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    return VoterTokenPackage.model_validate(data)


def save_vote_payload(path: Path, vote_payload: VoteCreate) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as file:
        json.dump(vote_payload.model_dump(mode="json"), file, indent=2)


def build_public_signals(
    voter_package: VoterTokenPackage,
    generated_proof: GeneratedProof,
) -> PublicSignals:
    nullifier_hash, election_id, merkle_root = generated_proof.public_signals
    parsed_election_id = int(election_id)

    if parsed_election_id != voter_package.election_id:
        raise ValueError("Generated proof has an unexpected election id.")

    if merkle_root != voter_package.merkle_root:
        raise ValueError("Generated proof has an unexpected Merkle root.")

    return PublicSignals(
        election_id=parsed_election_id,
        merkle_root=merkle_root,
        nullifier_hash=nullifier_hash,
    )


def build_circuit_input(
    voter_package: VoterTokenPackage,
) -> VoteCircuitInput:
    return VoteCircuitInput(
        token_secret=voter_package.token_secret,
        merkle_siblings=voter_package.merkle_proof.siblings,
        merkle_path_indices=[
            str(path_index)
            for path_index in voter_package.merkle_proof.path_indices
        ],
        election_id=str(voter_package.election_id),
        merkle_root=voter_package.merkle_root,
    )


def generate_vote_proof(circuit_input: VoteCircuitInput) -> GeneratedProof:
    return generate_groth16_proof(circuit_input.model_dump(mode="json"))


def build_vote_payload(
    voter_package: VoterTokenPackage,
    candidate_id: int,
) -> VoteCreate:
    circuit_input: VoteCircuitInput = build_circuit_input(voter_package)
    generated_proof: GeneratedProof = generate_vote_proof(circuit_input)
    public_signals: PublicSignals = build_public_signals(
        voter_package,
        generated_proof,
    )

    return VoteCreate(
        candidate_id=candidate_id,
        nullifier_hash=public_signals.nullifier_hash,
        proof=generated_proof.proof,
        public_signals=public_signals,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a demo vote payload from a voter token package.",
    )
    parser.add_argument(
        "--package",
        required=True,
        type=Path,
        help="Path to JSON file with VoterTokenPackage data.",
    )
    parser.add_argument(
        "--candidate-id",
        required=True,
        type=int,
        help="Candidate id selected by the voter.",
    )
    parser.add_argument(
        "--output",
        default=Path("vote_payload.json"),
        type=Path,
        help="Path where the generated vote payload should be saved.",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    voter_package = load_voter_package(args.package)
    vote_payload = build_vote_payload(voter_package, args.candidate_id)
    save_vote_payload(args.output, vote_payload)

    print(f"Vote payload saved to: {args.output}")


if __name__ == "__main__":
    main()
