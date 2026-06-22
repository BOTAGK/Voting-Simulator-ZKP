from pathlib import Path

import pytest

from app.core.exceptions import InvalidProofError
from app.services import zkp_service
from app.zkp.paths import ZkpArtifactPaths
from app.zkp.proof_models import PublicSignals


def build_public_signals() -> PublicSignals:
    return PublicSignals(
        election_id=7,
        merkle_root="999999",
        nullifier_hash="123456",
    )


def build_artifact_paths(tmp_path: Path) -> ZkpArtifactPaths:
    return ZkpArtifactPaths(
        artifacts_dir=tmp_path,
        circuit_path=tmp_path / "vote_eligibility.circom",
        wasm_path=tmp_path / "vote_eligibility.wasm",
        witness_generator_path=tmp_path / "generate_witness.js",
        zkey_path=tmp_path / "vote_eligibility_final.zkey",
        verification_key_path=tmp_path / "verification_key.json",
    )


def test_validate_public_signals_accepts_expected_values() -> None:
    zkp_service.validate_public_signals(
        public_signals=build_public_signals(),
        election_id=7,
        expected_merkle_root="999999",
        nullifier_hash="123456",
    )


def test_validate_public_signals_rejects_missing_merkle_root() -> None:
    with pytest.raises(InvalidProofError, match="Merkle root"):
        zkp_service.validate_public_signals(
            public_signals=build_public_signals(),
            election_id=7,
            expected_merkle_root=None,
            nullifier_hash="123456",
        )


def test_validate_public_signals_rejects_mismatched_values() -> None:
    with pytest.raises(InvalidProofError, match="Public signals"):
        zkp_service.validate_public_signals(
            public_signals=build_public_signals(),
            election_id=8,
            expected_merkle_root="999999",
            nullifier_hash="123456",
        )


def test_verify_proof_delegates_to_snarkjs_client(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    proof = {"pi_a": ["1", "2", "1"]}
    public_signals = build_public_signals()
    artifact_paths = build_artifact_paths(tmp_path)
    captured_call = {}

    def fake_verify_groth16_proof(
        received_proof,
        received_public_signals,
        artifact_paths=None,
    ) -> bool:
        captured_call["proof"] = received_proof
        captured_call["public_signals"] = received_public_signals
        captured_call["artifact_paths"] = artifact_paths
        return True

    monkeypatch.setattr(
        zkp_service,
        "verify_groth16_proof",
        fake_verify_groth16_proof,
    )

    assert zkp_service.verify_proof(
        proof,
        public_signals,
        artifact_paths=artifact_paths,
    )
    assert captured_call == {
        "proof": proof,
        "public_signals": public_signals,
        "artifact_paths": artifact_paths,
    }


def test_verify_proof_returns_false_when_snarkjs_rejects(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        zkp_service,
        "verify_groth16_proof",
        lambda proof, public_signals, artifact_paths=None: False,
    )

    assert not zkp_service.verify_proof(
        {"pi_a": ["bad"]},
        build_public_signals(),
    )
