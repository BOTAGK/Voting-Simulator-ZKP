import json
import subprocess
from pathlib import Path

import pytest

from app.core.exceptions import ZkpArtifactsMissingError
from app.zkp.paths import ZkpArtifactPaths, ensure_files_exist
from app.zkp.proof_models import PublicSignals
from app.zkp import snarkjs_client


def create_artifact_paths(tmp_path: Path) -> ZkpArtifactPaths:
    return ZkpArtifactPaths(
        artifacts_dir=tmp_path,
        circuit_path=tmp_path / "vote_eligibility.circom",
        wasm_path=tmp_path / "vote_eligibility.wasm",
        witness_generator_path=tmp_path / "generate_witness.js",
        zkey_path=tmp_path / "vote_eligibility_final.zkey",
        verification_key_path=tmp_path / "verification_key.json",
    )


def touch_required_files(paths: ZkpArtifactPaths) -> None:
    for path in [
        paths.wasm_path,
        paths.witness_generator_path,
        paths.zkey_path,
        paths.verification_key_path,
    ]:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("demo", encoding="utf-8")


def test_public_signals_to_snarkjs_uses_circuit_public_input_order() -> None:
    public_signals = PublicSignals(
        election_id=7,
        merkle_root="123",
        nullifier_hash="456",
    )

    assert snarkjs_client.public_signals_to_snarkjs(public_signals) == [
        "456",
        "7",
        "123",
    ]


def test_verify_groth16_proof_writes_expected_snarkjs_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths = create_artifact_paths(tmp_path)
    touch_required_files(paths)
    proof = {"pi_a": ["1", "2", "1"]}
    public_signals = PublicSignals(
        election_id=1,
        merkle_root="root",
        nullifier_hash="nullifier",
    )

    def fake_run_command(
        command: list[str],
        raise_on_error: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        assert Path(command[0]).name in ("snarkjs", "snarkjs.cmd")
        assert command[1:3] == ["groth16", "verify"]
        assert raise_on_error is False
        assert json.loads(Path(command[-2]).read_text(encoding="utf-8")) == [
            "nullifier",
            "1",
            "root",
        ]
        assert json.loads(Path(command[-1]).read_text(encoding="utf-8")) == proof

        return subprocess.CompletedProcess(command, 0, stdout="OK", stderr="")

    monkeypatch.setattr(snarkjs_client, "_run_command", fake_run_command)

    assert snarkjs_client.verify_groth16_proof(
        proof,
        public_signals,
        artifact_paths=paths,
    )


def test_verify_groth16_proof_returns_false_when_snarkjs_rejects(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths = create_artifact_paths(tmp_path)
    touch_required_files(paths)

    def fake_run_command(
        command: list[str],
        raise_on_error: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(command, 1, stdout="", stderr="Invalid")

    monkeypatch.setattr(snarkjs_client, "_run_command", fake_run_command)

    assert not snarkjs_client.verify_groth16_proof(
        proof={"pi_a": ["bad"]},
        public_signals=PublicSignals(
            election_id=1,
            merkle_root="root",
            nullifier_hash="nullifier",
        ),
        artifact_paths=paths,
    )


def test_generate_groth16_proof_returns_proof_and_public_signals(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths = create_artifact_paths(tmp_path)
    touch_required_files(paths)

    def fake_run_command(
        command: list[str],
        raise_on_error: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        if Path(command[0]).name in ("snarkjs", "snarkjs.cmd"):
            assert command[1:3] == ["groth16", "prove"]
            Path(command[-2]).write_text('{"pi_a":["1","2","1"]}', encoding="utf-8")
            Path(command[-1]).write_text('["1","2","3"]', encoding="utf-8")

        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(snarkjs_client, "_run_command", fake_run_command)

    generated_proof = snarkjs_client.generate_groth16_proof(
        {"token_secret": "123"},
        artifact_paths=paths,
    )

    assert generated_proof.proof == {"pi_a": ["1", "2", "1"]}
    assert generated_proof.public_signals == ["1", "2", "3"]


def test_ensure_files_exist_rejects_missing_artifact(tmp_path: Path) -> None:
    with pytest.raises(ZkpArtifactsMissingError, match="Missing ZKP artifact"):
        ensure_files_exist([tmp_path / "missing.zkey"])
