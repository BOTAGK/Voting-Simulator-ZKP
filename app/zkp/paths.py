from dataclasses import dataclass
from pathlib import Path
from typing import Final

from app.core.config import get_settings
from app.core.exceptions import ZkpArtifactsMissingError


PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
CIRCUITS_DIR: Final[Path] = PROJECT_ROOT / "circuits"
VOTE_CIRCUIT_NAME: Final[str] = "vote_eligibility"
VOTE_CIRCUIT_PATH: Final[Path] = CIRCUITS_DIR / f"{VOTE_CIRCUIT_NAME}.circom"


@dataclass(frozen=True)
class ZkpArtifactPaths:
    artifacts_dir: Path
    circuit_path: Path
    wasm_path: Path
    witness_generator_path: Path
    zkey_path: Path
    verification_key_path: Path

    def required_for_proving(self) -> list[Path]:
        return [
            self.wasm_path,
            self.witness_generator_path,
            self.zkey_path,
        ]

    def required_for_verification(self) -> list[Path]:
        return [self.verification_key_path]


def resolve_project_path(path_value: str | Path) -> Path:
    path = Path(path_value).expanduser()

    if not path.is_absolute():
        path = PROJECT_ROOT / path

    return path.resolve()


def get_zkp_artifacts_dir() -> Path:
    return resolve_project_path(get_settings().zkp_artifacts_dir)


def get_zkp_artifact_paths() -> ZkpArtifactPaths:
    artifacts_dir = get_zkp_artifacts_dir()
    circuit_js_dir = artifacts_dir / f"{VOTE_CIRCUIT_NAME}_js"

    return ZkpArtifactPaths(
        artifacts_dir=artifacts_dir,
        circuit_path=VOTE_CIRCUIT_PATH,
        wasm_path=circuit_js_dir / f"{VOTE_CIRCUIT_NAME}.wasm",
        witness_generator_path=circuit_js_dir / "generate_witness.js",
        zkey_path=artifacts_dir / f"{VOTE_CIRCUIT_NAME}_final.zkey",
        verification_key_path=artifacts_dir / "verification_key.json",
    )


def ensure_files_exist(paths: list[Path]) -> None:
    missing_paths = [path for path in paths if not path.exists()]

    if missing_paths:
        missing = ", ".join(str(path) for path in missing_paths)
        raise ZkpArtifactsMissingError(f"Missing ZKP artifact files: {missing}")
