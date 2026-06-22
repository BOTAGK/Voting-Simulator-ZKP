from typing import Any

from app.core.exceptions import InvalidProofError
from app.zkp.proof_models import PublicSignals
from app.zkp.paths import ZkpArtifactPaths
from app.zkp.snarkjs_client import verify_groth16_proof


def validate_public_signals(
    public_signals: PublicSignals,
    election_id: int,
    expected_merkle_root: str | None,
    nullifier_hash: str,
) -> None:
    if expected_merkle_root is None:
        raise InvalidProofError("Election Merkle root is missing.")

    expected_public_signals = PublicSignals(
        election_id=election_id,
        merkle_root=expected_merkle_root,
        nullifier_hash=nullifier_hash,
    )

    if public_signals != expected_public_signals:
        raise InvalidProofError("Public signals do not match vote data.")


def verify_proof(
    proof: dict[str, Any],
    public_signals: PublicSignals,
    artifact_paths: ZkpArtifactPaths | None = None,
) -> bool:
    return verify_groth16_proof(
        proof,
        public_signals,
        artifact_paths=artifact_paths,
    )
