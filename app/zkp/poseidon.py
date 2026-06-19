import json
import subprocess
from pathlib import Path
from typing import Final


BN254_FIELD_MODULUS: Final[int] = (
    21888242871839275222246405745257275088548364400416034343698204186575808495617
)

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
POSEIDON_CLI_PATH: Final[Path] = (
    PROJECT_ROOT / "scripts" / "poseidon_cli.mjs"
)


class PoseidonError(RuntimeError):
    """Raised when Poseidon hashing cannot be completed."""


def poseidon_hash(values: list[int]) -> int:
    return poseidon_hash_batch([values])[0]


def poseidon_hash_batch(inputs: list[list[int]]) -> list[int]:
    if not inputs:
        return []

    _validate_inputs(inputs)

    payload = json.dumps(
        [
            [str(value) for value in values]
            for values in inputs
        ]
    )

    try:
        result = subprocess.run(
            ["node", str(POSEIDON_CLI_PATH)],
            input=payload,
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
            timeout=30,
            check=False,
        )
    except FileNotFoundError as exc:
        raise PoseidonError(
            "Node.js was not found. Ensure that Node.js is installed."
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise PoseidonError("Poseidon calculation timed out.") from exc

    if result.returncode != 0:
        message = result.stderr.strip() or "Unknown Node.js error."
        raise PoseidonError(f"Poseidon calculation failed: {message}")

    try:
        output = json.loads(result.stdout)

        if not isinstance(output, list) or len(output) != len(inputs):
            raise ValueError("Unexpected number of Poseidon results.")

        return [int(value) for value in output]
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise PoseidonError(
            "Poseidon returned an invalid response."
        ) from exc


def _validate_inputs(inputs: list[list[int]]) -> None:
    for values in inputs:
        if not 1 <= len(values) <= 16:
            raise ValueError("Poseidon requires 1-16 inputs.")

        for value in values:
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError("Poseidon inputs must be integers.")

            if not 0 <= value < BN254_FIELD_MODULUS:
                raise ValueError(
                    "Poseidon input must belong to the BN254 field."
                )