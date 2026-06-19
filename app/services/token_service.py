import secrets
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.exceptions import DuplicateVoterTokenError, InvalidElectionStatusError
from app.models import Election, ElectionStatus, VoterToken
from app.repositories import voter_token_repository
from app.schemas.voter_token import (
    MerkleProofSchema,
    VoterTokenGenerateRequest,
    VoterTokenPackage,
)
from app.services.common import get_existing_election
from app.zkp.merkle import MerkleProof, MerkleTree
from app.zkp.poseidon import BN254_FIELD_MODULUS, poseidon_hash_batch


@dataclass(frozen=True)
class GeneratedToken:
    token_secret: int
    token_hash: int
    merkle_index: int
    merkle_root: int
    merkle_proof: MerkleProofSchema
    label_for_admin: str | None


def generate_voter_tokens(
    db: Session,
    election_id: int,
    data: VoterTokenGenerateRequest,
) -> list[VoterTokenPackage]:
    election: Election = get_election_ready_for_token_generation(db, election_id)
    ensure_tokens_were_not_generated(db, election_id)

    token_secrets: list[int] = generate_token_secrets(data.count)
    token_hashes: list[int] = hash_token_secrets(token_secrets)
    merkle_tree = MerkleTree(token_hashes)

    generated_tokens: list[GeneratedToken] = build_generated_tokens(
        token_secrets=token_secrets,
        token_hashes=token_hashes,
        merkle_tree=merkle_tree,
        label_prefix=data.label_prefix,
    )

    voter_tokens: list[VoterToken] = [
        build_voter_token_model(election_id, generated_token)
        for generated_token in generated_tokens
    ]

    voter_token_repository.bulk_create_voter_tokens(db, voter_tokens)
    save_merkle_root(db, election, merkle_tree.root)

    return [
        build_voter_token_package(election_id, generated_token)
        for generated_token in generated_tokens
    ]


def get_election_ready_for_token_generation(
    db: Session,
    election_id: int,
) -> Election:
    election: Election = get_existing_election(db, election_id)

    if election.status != ElectionStatus.DRAFT:
        raise InvalidElectionStatusError(
            "Voter tokens can only be generated for draft elections."
        )

    return election


def ensure_tokens_were_not_generated(db: Session, election_id: int) -> None:
    existing_tokens: list[VoterToken] = (
        voter_token_repository.list_voter_tokens_by_election(db, election_id)
    )

    if existing_tokens:
        raise DuplicateVoterTokenError(
            "Voter tokens have already been generated for this election."
        )


def generate_token_secret() -> int:
    return secrets.randbelow(BN254_FIELD_MODULUS - 1) + 1


def generate_token_secrets(count: int) -> list[int]:
    return [generate_token_secret() for _ in range(count)]


def hash_token_secrets(token_secrets: list[int]) -> list[int]:
    return poseidon_hash_batch([[token_secret] for token_secret in token_secrets])


def build_generated_tokens(
    token_secrets: list[int],
    token_hashes: list[int],
    merkle_tree: MerkleTree,
    label_prefix: str | None,
) -> list[GeneratedToken]:
    generated_tokens: list[GeneratedToken] = []

    for index, (token_secret, token_hash) in enumerate(
        zip(token_secrets, token_hashes, strict=True)
    ):
        proof: MerkleProof = merkle_tree.get_proof(index)
        merkle_proof = build_merkle_proof_schema(proof)

        generated_tokens.append(
            GeneratedToken(
                token_secret=token_secret,
                token_hash=token_hash,
                merkle_index=index,
                merkle_root=merkle_tree.root,
                merkle_proof=merkle_proof,
                label_for_admin=build_token_label(label_prefix, index),
            )
        )

    return generated_tokens


def build_voter_token_model(
    election_id: int,
    generated_token: GeneratedToken,
) -> VoterToken:
    return VoterToken(
        election_id=election_id,
        token_hash=str(generated_token.token_hash),
        merkle_index=generated_token.merkle_index,
        merkle_path_json=generated_token.merkle_proof.model_dump_json(),
        label_for_admin=generated_token.label_for_admin,
    )


def build_voter_token_package(
    election_id: int,
    generated_token: GeneratedToken,
) -> VoterTokenPackage:
    return VoterTokenPackage(
        election_id=election_id,
        token_secret=str(generated_token.token_secret),
        merkle_root=str(generated_token.merkle_root),
        merkle_index=generated_token.merkle_index,
        merkle_proof=generated_token.merkle_proof,
    )


def build_token_label(label_prefix: str | None, index: int) -> str | None:
    if label_prefix is None:
        return None

    return f"{label_prefix}-{index + 1}"


def build_merkle_proof_schema(proof: MerkleProof) -> MerkleProofSchema:
    return MerkleProofSchema(
        siblings=[str(sibling) for sibling in proof.siblings],
        path_indices=proof.path_indices,
    )

def save_merkle_root(db: Session, election: Election, merkle_root: int) -> None:
    election.merkle_root = str(merkle_root)
    db.commit()
    db.refresh(election)

def list_voter_tokens_for_election(
    db: Session,
    election_id: int,
) -> list[VoterToken]:
    get_existing_election(db, election_id)

    return voter_token_repository.list_voter_tokens_by_election(db, election_id)
