import json
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.core.exceptions import ZkpArtifactsMissingError
from app.zkp.paths import (
    PROJECT_ROOT,
    ZkpArtifactPaths,
    ensure_files_exist,
    get_zkp_artifact_paths,
)
from app.zkp.proof_models import PublicSignals


NODE_MODULES_BIN_DIR = PROJECT_ROOT / "node_modules" / ".bin"


class SnarkjsError(RuntimeError):
    """Raised when snarkjs command execution fails unexpectedly."""


@dataclass(frozen=True)
class GeneratedProof:
    proof: dict[str, Any]
    public_signals: list[str]


def generate_groth16_proof(
    input_data: dict[str, Any],
    artifact_paths: ZkpArtifactPaths | None = None,
) -> GeneratedProof:
    paths = artifact_paths or get_zkp_artifact_paths()
    ensure_files_exist(paths.required_for_proving())

    with tempfile.TemporaryDirectory() as temporary_dir:
        working_dir = Path(temporary_dir)
        input_path = working_dir / "input.json"
        witness_path = working_dir / "witness.wtns"
        proof_path = working_dir / "proof.json"
        public_signals_path = working_dir / "public.json"

        _write_json(input_path, input_data)

        _run_command(
            _node_command(
                [
                    str(paths.witness_generator_path),
                    str(paths.wasm_path),
                    str(input_path),
                    str(witness_path),
                ]
            )
        )
        _run_command(
            _snarkjs_command(
                [
                    "groth16",
                    "prove",
                    str(paths.zkey_path),
                    str(witness_path),
                    str(proof_path),
                    str(public_signals_path),
                ]
            )
        )

        return GeneratedProof(
            proof=_read_json_object(proof_path),
            public_signals=_read_json_list(public_signals_path),
        )


def verify_groth16_proof(
    proof: dict[str, Any],
    public_signals: PublicSignals,
    artifact_paths: ZkpArtifactPaths | None = None,
) -> bool:
    paths = artifact_paths or get_zkp_artifact_paths()
    ensure_files_exist(paths.required_for_verification())

    with tempfile.TemporaryDirectory() as temporary_dir:
        working_dir = Path(temporary_dir)
        proof_path = working_dir / "proof.json"
        public_signals_path = working_dir / "public.json"

        _write_json(proof_path, proof)
        _write_json(
            public_signals_path,
            public_signals_to_snarkjs(public_signals),
        )

        result = _run_command(
            _snarkjs_command(
                [
                    "groth16",
                    "verify",
                    str(paths.verification_key_path),
                    str(public_signals_path),
                    str(proof_path),
                ]
            ),
            raise_on_error=False,
        )

    return result.returncode == 0


def public_signals_to_snarkjs(public_signals: PublicSignals) -> list[str]:
    return [
        public_signals.nullifier_hash,
        str(public_signals.election_id),
        public_signals.merkle_root,
    ]


def _node_command(arguments: list[str]) -> list[str]:
    return [str(_resolve_executable("node", [])), *arguments]


def _snarkjs_command(arguments: list[str]) -> list[str]:
    return [
        str(
            _resolve_executable(
                "snarkjs",
                [
                    NODE_MODULES_BIN_DIR / "snarkjs.cmd",
                    NODE_MODULES_BIN_DIR / "snarkjs",
                ],
            )
        ),
        *arguments,
    ]


def _resolve_executable(
    executable_name: str,
    local_candidates: list[Path],
) -> Path:
    for candidate in local_candidates:
        if candidate.exists():
            return candidate

    resolved = shutil.which(executable_name)

    if resolved is not None and not _is_powershell_script(Path(resolved)):
        return Path(resolved)

    raise ZkpArtifactsMissingError(
        f"Could not execute {executable_name}. Check your ZKP setup."
    )


def _is_powershell_script(path: Path) -> bool:
    return os.name == "nt" and path.suffix.lower() == ".ps1"


def _run_command(
    command: list[str],
    raise_on_error: bool = True,
) -> subprocess.CompletedProcess[str]:
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
            timeout=60,
            check=False,
        )
    except FileNotFoundError as exc:
        raise ZkpArtifactsMissingError(
            "Could not execute Node.js or snarkjs. Check your ZKP setup."
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise SnarkjsError("snarkjs command timed out.") from exc

    if raise_on_error and result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "Unknown snarkjs error."
        raise SnarkjsError(message)

    return result


def _write_json(path: Path, data: Any) -> None:
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file)


def _read_json_object(path: Path) -> dict[str, Any]:
    data = _read_json(path)

    if not isinstance(data, dict):
        raise SnarkjsError(f"Expected JSON object in {path}.")

    return data


def _read_json_list(path: Path) -> list[str]:
    data = _read_json(path)

    if not isinstance(data, list):
        raise SnarkjsError(f"Expected JSON array in {path}.")

    return [str(value) for value in data]


def _read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)
