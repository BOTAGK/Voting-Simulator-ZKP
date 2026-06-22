from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.schemas.voter_token import VoterTokenPackage


def load_token_packages(path: Path) -> list[VoterTokenPackage]:
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if isinstance(data, list):
        return [VoterTokenPackage.model_validate(item) for item in data]

    return [VoterTokenPackage.model_validate(data)]


def extract_token_package(
    input_path: Path,
    output_path: Path,
    index: int,
) -> VoterTokenPackage:
    packages = load_token_packages(input_path)

    if index < 0 or index >= len(packages):
        available_range = f"0-{len(packages) - 1}" if packages else "empty"
        raise IndexError(
            f"Token index {index} is out of range. Available range: {available_range}."
        )

    package = packages[index]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(package.model_dump(mode="json"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return package


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract one voter token package from a JSON file."
    )
    parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="JSON file containing one token package or a list of token packages.",
    )
    parser.add_argument(
        "--index",
        default=0,
        type=int,
        help="Zero-based index of the token package to extract.",
    )
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Output path for the extracted token package JSON.",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    package = extract_token_package(args.input, args.output, args.index)
    print(
        f"Extracted token index {args.index} for election {package.election_id} "
        f"to: {args.output}"
    )


if __name__ == "__main__":
    main()
