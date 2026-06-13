class AppError(Exception):
    """Base class for domain-level application errors."""


class NotFoundError(AppError):
    """Raised when requested data does not exist."""


class ValidationError(AppError):
    """Raised when input data violates a business rule."""


class ElectionNotFoundError(NotFoundError):
    """Raised when an election does not exist."""


class CandidateNotFoundError(NotFoundError):
    """Raised when a candidate does not exist."""


class VoterTokenNotFoundError(NotFoundError):
    """Raised when a voter token does not exist."""


class VoteNotFoundError(NotFoundError):
    """Raised when a vote does not exist."""


class InvalidElectionDatesError(ValidationError):
    """Raised when election end date is not after start date."""


class InvalidElectionStatusError(ValidationError):
    """Raised when an operation is not allowed for election status."""


class CandidateElectionMismatchError(ValidationError):
    """Raised when candidate does not belong to selected election."""


class DuplicateNullifierError(ValidationError):
    """Raised when a nullifier was already used in an election."""


class DuplicateVoterTokenError(ValidationError):
    """Raised when a voter token hash already exists in an election."""


class InvalidProofError(ValidationError):
    """Raised when ZKP proof verification fails."""


class ZkpArtifactsMissingError(ValidationError):
    """Raised when required ZKP artifacts are missing."""