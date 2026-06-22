import csv as csv_module
import json
from io import StringIO

from pydantic import ValidationError as PydanticValidationError

from app.core.exceptions import InvalidCsvError
from app.schemas.candidate import CandidateCreate
from app.schemas.results import ElectionResultsRead
from app.schemas.voter_token import VoterTokenPackage


CANDIDATE_NAME_COLUMN = "name"
CANDIDATE_DESCRIPTION_COLUMN = "description"
CANDIDATE_CSV_REQUIRED_COLUMNS = {CANDIDATE_NAME_COLUMN}
CANDIDATE_CSV_ALLOWED_COLUMNS = {
    CANDIDATE_NAME_COLUMN,
    CANDIDATE_DESCRIPTION_COLUMN,
}
CSV_DIALECT_SAMPLE_LINES = 5
CSV_EXPORT_DELIMITER = ";"
VOTER_TOKEN_CSV_COLUMNS = [
    "election_id",
    "token_secret",
    "merkle_root",
    "merkle_index",
    "merkle_siblings",
    "merkle_path_indices",
]
ELECTION_RESULTS_CSV_COLUMNS = [
    "election_id",
    "election_name",
    "status",
    "total_votes",
    "total_tokens",
    "turnout",
    "candidate_id",
    "candidate_name",
    "votes",
]


def parse_candidates_csv(content: bytes) -> list[CandidateCreate]:
    text = _decode_csv_content(content)
    reader = csv_module.DictReader(StringIO(text), dialect=_detect_dialect(text))
    _normalize_headers(reader)
    _validate_candidate_headers(reader.fieldnames)

    candidates: list[CandidateCreate] = []

    for row_number, row in enumerate(reader, start=2):
        _validate_candidate_row_shape(row, row_number)

        if _is_blank_row(row):
            continue

        try:
            candidates.append(
                CandidateCreate(
                    name=(row.get(CANDIDATE_NAME_COLUMN) or "").strip(),
                    description=_empty_to_none(
                        row.get(CANDIDATE_DESCRIPTION_COLUMN)
                    ),
                )
            )
        except PydanticValidationError as exc:
            raise InvalidCsvError(
                f"Invalid candidate data in CSV row {row_number}."
            ) from exc

    if not candidates:
        raise InvalidCsvError("CSV file does not contain any candidates.")

    return candidates


def build_voter_token_packages_csv(packages: list[VoterTokenPackage]) -> str:
    output = StringIO()
    writer = _build_export_writer(output, VOTER_TOKEN_CSV_COLUMNS)
    writer.writeheader()

    for package in packages:
        writer.writerow(
            {
                "election_id": package.election_id,
                "token_secret": package.token_secret,
                "merkle_root": package.merkle_root,
                "merkle_index": package.merkle_index,
                "merkle_siblings": json.dumps(package.merkle_proof.siblings),
                "merkle_path_indices": json.dumps(
                    package.merkle_proof.path_indices
                ),
            }
        )

    return output.getvalue()


def build_election_results_csv(results: ElectionResultsRead) -> str:
    output = StringIO()
    writer = _build_export_writer(output, ELECTION_RESULTS_CSV_COLUMNS)
    writer.writeheader()

    for candidate_result in results.results:
        writer.writerow(
            {
                "election_id": results.election_id,
                "election_name": results.election_name,
                "status": results.status,
                "total_votes": results.total_votes,
                "total_tokens": results.total_tokens,
                "turnout": results.turnout,
                "candidate_id": candidate_result.candidate_id,
                "candidate_name": candidate_result.candidate_name,
                "votes": candidate_result.votes,
            }
        )

    return output.getvalue()


def _build_export_writer(
    output: StringIO,
    fieldnames: list[str],
) -> csv_module.DictWriter:
    return csv_module.DictWriter(
        output,
        fieldnames=fieldnames,
        delimiter=CSV_EXPORT_DELIMITER,
        lineterminator="\n",
    )


def _decode_csv_content(content: bytes) -> str:
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise InvalidCsvError("CSV file must be encoded as UTF-8.") from exc

    if not text.strip():
        raise InvalidCsvError("CSV file is empty.")

    return text


def _detect_dialect(text: str) -> csv_module.Dialect:
    sample = "\n".join(text.splitlines()[:CSV_DIALECT_SAMPLE_LINES])

    try:
        return csv_module.Sniffer().sniff(sample, delimiters=",;")
    except csv_module.Error:
        return csv_module.excel


def _normalize_headers(reader: csv_module.DictReader) -> None:
    if reader.fieldnames is None:
        return

    reader.fieldnames = [header.strip() for header in reader.fieldnames]


def _validate_candidate_headers(headers: list[str] | None) -> None:
    if headers is None:
        raise InvalidCsvError("CSV file must contain a header row.")

    normalized_headers = {header.strip() for header in headers if header}
    missing_columns = CANDIDATE_CSV_REQUIRED_COLUMNS - normalized_headers
    unsupported_columns = normalized_headers - CANDIDATE_CSV_ALLOWED_COLUMNS

    if missing_columns:
        columns = ", ".join(f"'{column}'" for column in sorted(missing_columns))
        raise InvalidCsvError(
            f"CSV file is missing required columns: {columns}."
        )

    if unsupported_columns:
        columns = ", ".join(sorted(unsupported_columns))
        raise InvalidCsvError(f"CSV file contains unsupported columns: {columns}.")


def _validate_candidate_row_shape(
    row: dict[str | None, str | list[str] | None],
    row_number: int,
) -> None:
    if None in row:
        raise InvalidCsvError(
            f"CSV row {row_number} contains more values than the header row."
        )


def _is_blank_row(row: dict[str, str | None]) -> bool:
    return all(not (value or "").strip() for value in row.values())


def _empty_to_none(value: str | None) -> str | None:
    if value is None:
        return None

    stripped_value = value.strip()
    return stripped_value or None
